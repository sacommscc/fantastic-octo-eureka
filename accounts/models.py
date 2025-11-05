"""Accounts domain models."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from typing import Optional

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

mnemonic_validator = RegexValidator(
    regex=r"^(\w+\s){23}\w+$",
    message="Mnemonic phrase must contain exactly 24 words.",
)


class UserManager(BaseUserManager):
    """Custom user manager eliminating the email requirement."""

    use_in_migrations = True

    def _create_user(self, username: str, password: Optional[str], **extra_fields):
        if not username:
            raise ValueError("The username must be set")

        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, username: str, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("security_level", User.SecurityLevel.ADMIN.value)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, password, **extra_fields)


class User(AbstractUser):
    """Primary user model with mnemonic-based recovery."""

    class NotificationChannel(models.TextChoices):
        JABBER = "jabber", "Jabber/XMPP"
        TELEGRAM = "telegram", "Telegram"

    class SecurityLevel(models.IntegerChoices):
        BASIC = 1, "Basic"
        ENHANCED = 2, "Enhanced"
        ADMIN = 3, "Administrator"

    xmpp_address = models.CharField(
        max_length=255,
        blank=True,
        help_text="User's Jabber/XMPP address used for notifications.",
    )
    telegram_username = models.CharField(
        max_length=150,
        blank=True,
        help_text="Telegram username without the leading @.",
    )
    telegram_chat_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="Resolved Telegram chat ID for direct messages.",
    )
    preferred_channel = models.CharField(
        max_length=16,
        choices=NotificationChannel.choices,
        default=NotificationChannel.TELEGRAM,
    )
    security_level = models.PositiveSmallIntegerField(
        choices=SecurityLevel.choices,
        default=SecurityLevel.BASIC,
    )
    requires_mfa = models.BooleanField(default=False)
    jabber_verified = models.BooleanField(default=False)
    telegram_verified = models.BooleanField(default=False)

    mnemonic_salt = models.BinaryField(null=True, blank=True, editable=False)
    mnemonic_hash = models.CharField(max_length=128, blank=True, editable=False)
    mnemonic_created_at = models.DateTimeField(null=True, blank=True, editable=False)
    mnemonic_hint = models.CharField(
        max_length=128,
        blank=True,
        help_text="Non-sensitive hint to help the user recall their seed.",
    )
    recovery_attempts = models.PositiveSmallIntegerField(default=0)
    last_recovery_attempt = models.DateTimeField(null=True, blank=True)

    session_limit = models.PositiveSmallIntegerField(default=5)

    objects = UserManager()

    EMAIL_FIELD = ""
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: list[str] = []

    def set_mnemonic_phrase(self, phrase: str) -> None:
        mnemonic_validator(phrase)
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha3-256", phrase.encode("utf-8"), salt, 390000)
        self.mnemonic_salt = salt
        self.mnemonic_hash = digest.hex()
        self.mnemonic_created_at = timezone.now()
        self.recovery_attempts = 0
        self.mnemonic_hint = phrase.split()[0]

    def check_mnemonic_phrase(self, phrase: str) -> bool:
        if not self.mnemonic_hash or not self.mnemonic_salt:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha3-256",
            phrase.encode("utf-8"),
            bytes(self.mnemonic_salt),
            390000,
        )
        return digest.hex() == self.mnemonic_hash

    def can_attempt_recovery(self) -> bool:
        if self.recovery_attempts < 5:
            return True
        if not self.last_recovery_attempt:
            return True
        return timezone.now() - self.last_recovery_attempt > timedelta(hours=12)

    def register_recovery_attempt(self, success: bool) -> None:
        self.last_recovery_attempt = timezone.now()
        if success:
            self.recovery_attempts = 0
            type(self).objects.filter(pk=self.pk).update(
                last_recovery_attempt=self.last_recovery_attempt,
                recovery_attempts=0,
            )
        else:
            type(self).objects.filter(pk=self.pk).update(
                last_recovery_attempt=self.last_recovery_attempt,
                recovery_attempts=models.F("recovery_attempts") + 1,
            )
            self.refresh_from_db(fields=["recovery_attempts"])



class RecoverySession(models.Model):
    """Track mnemonic-driven password recovery flows."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recovery_sessions")
    mnemonic_confirmed = models.BooleanField(default=False)
    otp_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    channel_used = models.CharField(
        max_length=16,
        choices=User.NotificationChannel.choices,
        default=User.NotificationChannel.TELEGRAM,
    )

    def mark_verified(self) -> None:
        self.status = self.Status.VERIFIED
        self.save(update_fields=["status"])

    def mark_expired(self) -> None:
        self.status = self.Status.EXPIRED
        self.save(update_fields=["status"])

    def is_active(self) -> bool:
        return self.status == self.Status.PENDING and timezone.now() < self.expires_at


class ActiveSession(models.Model):
    """Stores metadata about user sessions for security tracking."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=64, unique=True)
    user_agent = models.CharField(max_length=512, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-last_seen"]

    def terminate(self) -> None:
        self.is_active = False
        self.save(update_fields=["is_active"])

