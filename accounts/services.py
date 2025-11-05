"""Service layer for accounts domain."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from django.utils import timezone

from mnemonic import Mnemonic

from notifications.dispatch import NotificationDispatchService

from .models import RecoverySession, User


mnemonic_generator = Mnemonic("english")


def generate_mnemonic_phrase() -> str:
    return mnemonic_generator.generate(strength=256)


@dataclass
class RecoveryChallenge:
    recovery_session: RecoverySession
    otp_code: str


class RecoveryOrchestrator:
    """Coordinates mnemonic + OTP recovery flows."""

    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 15

    def __init__(self, notification_service: Optional[NotificationDispatchService] = None):
        self.notification_service = notification_service or NotificationDispatchService()

    def initiate_session(self, user: User) -> RecoveryChallenge:
        expires_at = timezone.now() + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        session = RecoverySession.objects.create(
            user=user,
            expires_at=expires_at,
            channel_used=user.preferred_channel,
        )

        otp = self._issue_one_time_code()
        self.notification_service.send_recovery_otp(user, otp)

        return RecoveryChallenge(recovery_session=session, otp_code=otp)

    def _issue_one_time_code(self) -> str:
        return "".join(secrets.choice("0123456789") for _ in range(self.OTP_LENGTH))

