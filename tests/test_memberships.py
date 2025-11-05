from decimal import Decimal

import pytest

from django.contrib.auth import get_user_model

from memberships.models import MembershipGroup, MembershipPlan, UserMembership
from memberships.services import MembershipService
from wallets.models import Currency, WalletAccount


@pytest.mark.django_db
def test_purchase_membership_with_wallet():
    User = get_user_model()
    user = User.objects.create_user(username="member", password="password123")

    currency = Currency.objects.create(code="USDT", name="Tether", precision=2, is_crypto=True)
    group = MembershipGroup.objects.create(name="Level One", slug="level-one", level=1)
    plan = MembershipPlan.objects.create(
        group=group,
        name="Starter",
        currency=currency,
        amount=Decimal("10"),
        interval=MembershipPlan.BillingInterval.MONTHLY,
        duration_days=30,
    )

    wallet = WalletAccount.objects.create(user=user, currency=currency, balance=Decimal("20"), available_balance=Decimal("20"))

    membership = MembershipService().purchase_plan(user, plan, wallet)

    membership.refresh_from_db()
    wallet.refresh_from_db()

    assert membership.status == UserMembership.Status.ACTIVE
    assert wallet.balance == Decimal("10")
    assert wallet.available_balance == Decimal("10")
