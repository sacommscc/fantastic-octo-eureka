"""Admin registrations for infrastructure monitoring."""

from __future__ import annotations

from django.contrib import admin

from .models import BackupLog, ServiceStatus, SystemMetric


@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "last_checked")
    search_fields = ("name",)


@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ("executed_at", "status", "location")
    list_filter = ("status",)
    search_fields = ("location",)


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "unit", "captured_at")
    list_filter = ("name",)
    search_fields = ("name",)

