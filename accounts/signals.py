"""Signal handlers for accounts."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import ActiveSession


User = get_user_model()


def _get_user_agent(request) -> str:
    return request.META.get("HTTP_USER_AGENT", "")[:512]


def _get_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def track_login(sender, request, user: User, **kwargs):  # pragma: no cover - signal
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    ActiveSession.objects.update_or_create(
        user=user,
        session_key=session_key,
        defaults={
            "user_agent": _get_user_agent(request),
            "ip_address": _get_ip(request),
            "is_active": True,
        },
    )

    active_sessions = list(user.sessions.filter(is_active=True).order_by("-last_seen"))
    for session in active_sessions[user.session_limit :]:
        session.terminate()


@receiver(user_logged_out)
def track_logout(sender, request, user: User, **kwargs):  # pragma: no cover - signal
    if not user.is_authenticated:
        return
    session_key = getattr(request.session, "session_key", None)
    if not session_key:
        return
    ActiveSession.objects.filter(user=user, session_key=session_key).update(is_active=False)

