"""Support and messaging models."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class TicketCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    sla_hours = models.PositiveIntegerField(default=24)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - admin display
        return self.name


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets")
    subject = models.CharField(max_length=200)
    category = models.ForeignKey(TicketCategory, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.NORMAL)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - admin display
        return f"#{self.pk} {self.subject}"

    def add_message(self, author, body: str, attachment=None) -> "TicketMessage":
        message = TicketMessage.objects.create(ticket=self, author=author, body=body)
        if attachment:
            TicketAttachment.objects.create(message=message, file=attachment)
        self.updated_at = timezone.now()
        self.save(update_fields=["updated_at"])
        return message

    def close(self, resolved_by=None) -> None:
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        if resolved_by:
            self.assigned_to = resolved_by
        self.save(update_fields=["status", "closed_at", "assigned_to", "updated_at"])


class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ticket_messages")
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover - admin display
        return f"Message<{self.ticket_id}>"


def attachment_upload_to(instance, filename):  # pragma: no cover - deterministic path
    return f"support/{instance.message.ticket_id}/{filename}"


class TicketAttachment(models.Model):
    message = models.ForeignKey(TicketMessage, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_upload_to)
    uploaded_at = models.DateTimeField(auto_now_add=True)

