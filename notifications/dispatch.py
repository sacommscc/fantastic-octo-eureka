"""Notification dispatch layer."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.template import Template, Context

from telegram import Bot
from telegram.error import TelegramError

from .models import NotificationLog, NotificationPreference, NotificationTemplate


logger = logging.getLogger(__name__)


def render_template(body: str, context: dict[str, Any]) -> str:
    template = Template(body)
    return template.render(Context(context))


class NotificationDispatchService:
    """Facade orchestrating outgoing notifications."""

    def __init__(self, telegram_token: str | None = None):
        self.telegram_token = telegram_token or settings.TELEGRAM_BOT_TOKEN

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def send_recovery_otp(self, user, otp_code: str) -> NotificationLog:
        context = {
            "username": user.username,
            "otp": otp_code,
        }
        default_message = f"Your password reset code is {otp_code}. It expires in 15 minutes."
        return self.send_event(
            user=user,
            event_code="accounts.recovery.otp",
            context=context,
            fallback_body=default_message,
        )

    def send_event(
        self,
        user,
        event_code: str,
        context: dict[str, Any],
        fallback_body: str = "",
        channel: str | None = None,
    ) -> NotificationLog:
        channel = channel or user.preferred_channel
        template = NotificationTemplate.objects.filter(
            code=event_code,
            channel=channel,
            is_active=True,
        ).first()

        body = fallback_body
        if template:
            body = render_template(template.body, context)

        log = NotificationLog.objects.create(
            user=user,
            channel=channel,
            template=template,
            payload=context,
        )

        if not self._is_enabled(user, channel):
            log.mark_failed("Channel disabled by user preference")
            return log

        try:
            if channel == NotificationTemplate.Channel.TELEGRAM:
                self._send_telegram(user, body)
            elif channel == NotificationTemplate.Channel.JABBER:
                self._send_jabber(user, body)
            else:
                raise ValueError(f"Unsupported channel {channel}")
        except Exception as exc:  # pragma: no cover - network dependent
            logger.exception("Notification send failure")
            log.mark_failed(str(exc))
        else:
            log.mark_sent()

        return log

    # ------------------------------------------------------------------
    # Transport implementations
    # ------------------------------------------------------------------

    def _send_telegram(self, user, message: str) -> None:
        if not self.telegram_token:
            raise RuntimeError("Telegram bot token not configured")

        chat_id = user.telegram_chat_id
        if not chat_id:
            raise RuntimeError("Telegram chat id missing; ensure the user initiated the bot")

        bot = Bot(token=self.telegram_token)
        try:
            bot.send_message(chat_id=chat_id, text=message)
        except TelegramError as exc:
            raise RuntimeError(f"Telegram send failed: {exc}") from exc

    def _send_jabber(self, user, message: str) -> None:
        # TODO: integrate actual Jabber/XMPP send logic via slixmpp.
        if not user.xmpp_address:
            raise RuntimeError("Jabber address missing")
        logger.info("Simulated Jabber message to %s: %s", user.xmpp_address, message)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _is_enabled(self, user, channel: str) -> bool:
        try:
            preference = NotificationPreference.objects.get(user=user, channel=channel)
        except NotificationPreference.DoesNotExist:
            return True
        return preference.enabled

