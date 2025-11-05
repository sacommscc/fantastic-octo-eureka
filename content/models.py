"""Content and notices models."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from memberships.models import MembershipGroup


class NewsItem(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("published", "Published"),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    publish_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="news_created")
    target_groups = models.ManyToManyField(MembershipGroup, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publish_at", "-created_at"]

    def __str__(self) -> str:  # pragma: no cover - admin display
        return self.title

    @property
    def is_visible(self) -> bool:
        if self.status == "published":
            return True
        if self.status == "scheduled" and self.publish_at:
            return timezone.now() >= self.publish_at
        return False


class Notice(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_sticky = models.BooleanField(default=False)
    target_groups = models.ManyToManyField(MembershipGroup, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="notices_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_sticky", "-start_at"]

    def __str__(self) -> str:  # pragma: no cover - admin display
        return self.title

    def is_visible(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_at and now < self.start_at:
            return False
        if self.end_at and now > self.end_at:
            return False
        return True

