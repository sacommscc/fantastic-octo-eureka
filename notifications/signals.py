"""Signals for notifications."""

from __future__ import annotations

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import NotificationPreference, NotificationTemplate


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_notification_preferences(sender, instance, created, **kwargs):  # pragma: no cover - signal
    if not created:
        return
    for channel, _ in NotificationTemplate.Channel.choices:
        NotificationPreference.objects.get_or_create(user=instance, channel=channel)

