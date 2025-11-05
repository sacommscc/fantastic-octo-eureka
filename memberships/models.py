"""Membership and access models."""

from __future__ import annotations

from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from wallets.models import Currency, WalletTransaction


class MembershipGroup(models.Model):
    """User grouping tied to access control."""

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    level = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    color = models.CharField(max_length=12, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["level", "name"]

    def __str__(self) -> str:  # pragma: no cover - admin
        return self.name


class MembershipPlan(models.Model):
    """Priced plan associated with a group."""

    class BillingInterval(models.TextChoices):
        LIFETIME = "lifetime", "Lifetime"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        YEARLY = "yearly", "Yearly"

    group = models.ForeignKey(MembershipGroup, on_delete=models.CASCADE, related_name="plans")
    name = models.CharField(max_length=150)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    interval = models.CharField(max_length=16, choices=BillingInterval.choices, default=BillingInterval.MONTHLY)
    duration_days = models.PositiveIntegerField(help_text="Number of days membership remains active.")
    is_active = models.BooleanField(default=True)
    allow_upgrade_to = models.ManyToManyField("self", symmetrical=False, blank=True, related_name="upgrade_from")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("group", "name", "currency")
        ordering = ["group__level", "amount"]

    def __str__(self) -> str:  # pragma: no cover - admin
        return f"{self.group.name} - {self.name}"


class MembershipUpgradeRule(models.Model):
    """Defines the fee logic when moving between plans."""

    from_plan = models.ForeignKey(MembershipPlan, on_delete=models.CASCADE, related_name="upgrade_rules_from")
    to_plan = models.ForeignKey(MembershipPlan, on_delete=models.CASCADE, related_name="upgrade_rules_to")
    additional_cost = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))
    description = models.TextField(blank=True)
    prorate_remaining = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("from_plan", "to_plan")

    def __str__(self) -> str:  # pragma: no cover - admin
        return f"{self.from_plan} -> {self.to_plan}"


class AccessArea(models.Model):
    """Permission rule for a group."""

    group = models.ForeignKey(MembershipGroup, on_delete=models.CASCADE, related_name="access_rules")
    resource = models.CharField(max_length=150)
    action = models.CharField(max_length=150)
    allowed = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("group", "resource", "action")

    def __str__(self):  # pragma: no cover - admin
        return f"{self.group.slug}:{self.resource}:{self.action}"


class UserMembership(models.Model):
    """Represents a user's purchased membership."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    auto_renew = models.BooleanField(default=False)
    last_transaction = models.ForeignKey(
        WalletTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membership_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-expires_at"]
        unique_together = ("user", "plan", "status", "expires_at")

    def __str__(self):  # pragma: no cover - admin
        return f"{self.user} -> {self.plan} ({self.status})"

    def activate(self, transaction: WalletTransaction | None = None) -> None:
        self.status = self.Status.ACTIVE
        if transaction:
            self.last_transaction = transaction
        self.started_at = timezone.now()
        self.expires_at = self.started_at + timedelta(days=self.plan.duration_days)
        self.save(update_fields=["status", "last_transaction", "started_at", "expires_at", "updated_at"])

    def cancel(self) -> None:
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status", "updated_at"])

    def mark_expired(self) -> None:
        self.status = self.Status.EXPIRED
        self.save(update_fields=["status", "updated_at"])


class MembershipInvoice(models.Model):
    """Stores membership payment intents."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membership_invoices")
    plan = models.ForeignKey(MembershipPlan, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    status = models.CharField(
        max_length=16,
        choices=[
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("refunded", "Refunded"),
        ],
        default="pending",
    )
    transaction = models.ForeignKey(
        WalletTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membership_invoices",
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

