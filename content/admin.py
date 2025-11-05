"""Admin registration for content management."""

from __future__ import annotations

from django.contrib import admin

from .models import NewsItem, Notice


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "publish_at", "created_by", "updated_at")
    list_filter = ("status", "publish_at")
    search_fields = ("title", "summary")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("target_groups",)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "is_sticky", "start_at", "end_at")
    list_filter = ("is_active", "is_sticky")
    search_fields = ("title", "body")
    filter_horizontal = ("target_groups",)

