"""Service layer for memberships."""

from __future__ import annotations

from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from wallets.models import WalletAccount

from .models import MembershipInvoice, MembershipPlan, MembershipUpgradeRule, UserMembership


class MembershipService:
    """Encapsulates membership billing workflows."""

    def purchase_plan(self, user, plan: MembershipPlan, wallet_account: WalletAccount) -> UserMembership:
        if wallet_account.currency_id != plan.currency_id:
            raise ValueError("Wallet currency mismatch")

        invoice = MembershipInvoice.objects.create(
            user=user,
            plan=plan,
            currency=plan.currency,
            amount=plan.amount,
            status="pending",
        )

        with transaction.atomic():
            account = WalletAccount.objects.select_for_update().get(pk=wallet_account.pk)
            tx = account.debit(plan.amount, reference=f"membership:{plan.pk}")
            invoice.transaction = tx
            invoice.status = "completed"
            invoice.save(update_fields=["transaction", "status", "updated_at"])

            membership = UserMembership.objects.create(
                user=user,
                plan=plan,
                status=UserMembership.Status.PENDING,
                started_at=tx.created_at,
                expires_at=tx.created_at,
            )
            membership.activate(transaction=tx)

        return membership

    def upgrade_membership(
        self,
        membership: UserMembership,
        target_plan: MembershipPlan,
        wallet_account: WalletAccount,
    ) -> UserMembership:
        if membership.plan == target_plan:
            raise ValueError("Already on this plan")

        rule = MembershipUpgradeRule.objects.filter(from_plan=membership.plan, to_plan=target_plan, is_active=True).first()
        if not rule:
            raise ValueError("Upgrade not permitted")

        if wallet_account.currency_id != target_plan.currency_id:
            raise ValueError("Wallet currency mismatch")

        cost = rule.additional_cost
        if cost <= 0:
            cost = target_plan.amount - membership.plan.amount
        cost = max(Decimal("0"), cost)

        with transaction.atomic():
            account = WalletAccount.objects.select_for_update().get(pk=wallet_account.pk)
            tx = account.debit(cost, reference=f"membership-upgrade:{membership.pk}")

            membership.plan = target_plan
            membership.last_transaction = tx
            membership.status = UserMembership.Status.ACTIVE
            membership.save(update_fields=["plan", "last_transaction", "status", "updated_at"])
            membership.activate(transaction=tx)

        return membership

