"""Forms for infrastructure module."""

from __future__ import annotations

from django import forms

from .models import BackupLog, ServiceStatus


class ServiceStatusForm(forms.ModelForm):
    class Meta:
        model = ServiceStatus
        fields = ("name", "status", "message")


class BackupLogForm(forms.ModelForm):
    class Meta:
        model = BackupLog
        fields = ("location", "status", "notes")

