"""Forms for content management."""

from __future__ import annotations

from django import forms

from .models import NewsItem, Notice


class NewsItemForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        fields = (
            "title",
            "slug",
            "summary",
            "body",
            "status",
            "publish_at",
            "target_groups",
        )
        widgets = {
            "publish_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "body": forms.Textarea(attrs={"rows": 6}),
        }


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = (
            "title",
            "body",
            "start_at",
            "end_at",
            "is_active",
            "is_sticky",
            "target_groups",
        )
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "body": forms.Textarea(attrs={"rows": 6}),
        }

