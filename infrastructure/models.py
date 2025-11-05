"""Infrastructure health models."""

from __future__ import annotations

from django.db import models
from django.utils import timezone


class ServiceStatus(models.Model):
    name = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=32, default="unknown")
    message = models.TextField(blank=True)
    last_checked = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):  # pragma: no cover - admin display
        return f"{self.name}: {self.status}"


class BackupLog(models.Model):
    executed_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=32, default="pending")
    location = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-executed_at"]


class SystemMetric(models.Model):
    name = models.CharField(max_length=120)
    value = models.FloatField()
    unit = models.CharField(max_length=24, blank=True)
    captured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-captured_at"]
