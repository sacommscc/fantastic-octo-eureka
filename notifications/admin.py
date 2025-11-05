"""Notification admin registrations."""

from __future__ import annotations

from django.contrib import admin

from .models import NotificationLog, NotificationPreference, NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "channel", "is_active", "updated_at")
    list_filter = ("channel", "is_active")
    search_fields = ("code", "subject")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "channel", "enabled", "updated_at")
    list_filter = ("channel", "enabled")
    search_fields = ("user__username",)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "channel", "status", "created_at", "sent_at")
    list_filter = ("channel", "status", "created_at")
    search_fields = ("user__username", "payload")
    readonly_fields = ("payload",)

