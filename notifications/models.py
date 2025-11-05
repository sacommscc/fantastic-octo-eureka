"""Notification system models."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationTemplate(models.Model):
    """Reusable notification templates per channel."""

    class Channel(models.TextChoices):
        JABBER = "jabber", "Jabber/XMPP"
        TELEGRAM = "telegram", "Telegram"

    code = models.CharField(max_length=128, unique=True)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover - admin display
        return f"{self.code} ({self.channel})"


class NotificationPreference(models.Model):
    """Per-user channel toggle."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences")
    channel = models.CharField(max_length=16, choices=NotificationTemplate.Channel.choices)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "channel")

    def __str__(self) -> str:  # pragma: no cover - admin display
        return f"Preference<{self.user}:{self.channel}:{self.enabled}>"


class NotificationLog(models.Model):
    """Audit of notifications sent to users."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_logs")
    channel = models.CharField(max_length=16, choices=NotificationTemplate.Channel.choices)
    template = models.ForeignKey(NotificationTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_sent(self) -> None:
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.error_message = ""
        self.save(update_fields=["status", "sent_at", "error_message"])

    def mark_failed(self, error: str) -> None:
        self.status = self.Status.FAILED
        self.error_message = error
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at", "error_message"])

