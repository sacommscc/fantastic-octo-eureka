"""Admin configuration for support tickets."""

from __future__ import annotations

from django.contrib import admin

from .models import SupportTicket, TicketAttachment, TicketCategory, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ("author", "body", "created_at")


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sla_hours", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "user", "status", "priority", "created_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("subject", "user__username")
    inlines = [TicketMessageInline]


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ("message", "uploaded_at")
    search_fields = ("message__ticket__subject",)

