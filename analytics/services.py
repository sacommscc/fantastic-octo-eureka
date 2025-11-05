"""Analytics aggregation helpers."""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from accounts.models import User
from memberships.models import MembershipInvoice, UserMembership
from support.models import SupportTicket
from wallets.models import WalletTransaction


def membership_summary():
    now = timezone.now()
    month_ago = now - timedelta(days=30)
    return {
        "total_users": User.objects.count(),
        "active_memberships": UserMembership.objects.filter(status=UserMembership.Status.ACTIVE).count(),
        "new_memberships": UserMembership.objects.filter(created_at__gte=month_ago).count(),
        "revenue_last_30_days": MembershipInvoice.objects.filter(
            status="completed",
            created_at__gte=month_ago,
        ).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0,
    }


def wallet_summary():
    month_ago = timezone.now() - timedelta(days=30)
    txs = WalletTransaction.objects.filter(created_at__gte=month_ago, status=WalletTransaction.Status.CONFIRMED)
    return {
        "credits": txs.filter(direction=WalletTransaction.Direction.CREDIT).aggregate(total=Sum("amount"))["total"] or 0,
        "debits": txs.filter(direction=WalletTransaction.Direction.DEBIT).aggregate(total=Sum("amount"))["total"] or 0,
    }


def support_summary():
    return (
        SupportTicket.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

