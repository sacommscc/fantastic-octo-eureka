"""Custom admin registrations for accounts."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import ActiveSession, RecoverySession, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Notification"),
            {
                "fields": (
                    "preferred_channel",
                    "xmpp_address",
                    "jabber_verified",
                    "telegram_username",
                    "telegram_chat_id",
                    "telegram_verified",
                )
            },
        ),
        (
            _("Security"),
            {
                "fields": (
                    "security_level",
                    "requires_mfa",
                    "session_limit",
                    "mnemonic_hint",
                    "mnemonic_created_at",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "preferred_channel"),
            },
        ),
    )

    list_display = (
        "username",
        "security_level",
        "preferred_channel",
        "jabber_verified",
        "telegram_verified",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "security_level",
        "preferred_channel",
    )
    search_fields = ("username", "xmpp_address", "telegram_username")
    ordering = ("username",)


@admin.register(ActiveSession)
class ActiveSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "session_key", "ip_address", "last_seen", "is_active")
    list_filter = ("is_active", "created_at")
    search_fields = ("user__username", "ip_address", "session_key")


@admin.register(RecoverySession)
class RecoverySessionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "status",
        "channel_used",
        "created_at",
        "expires_at",
    )
    list_filter = ("status", "channel_used", "created_at")
    search_fields = ("user__username",)
