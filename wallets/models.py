"""Wallet and payments models."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Currency(models.Model):
    """Supported currency definitions."""

    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=64)
    precision = models.PositiveSmallIntegerField(default=8)
    is_crypto = models.BooleanField(default=True)
    network = models.CharField(max_length=64, blank=True)
    symbol = models.CharField(max_length=12, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover - admin display
        return f"{self.code}"


class NodeConfiguration(models.Model):
    """Self-hosted node endpoint configuration."""

    currency = models.OneToOneField(Currency, on_delete=models.CASCADE, related_name="node")
    rpc_url = models.URLField()
    rpc_username = models.CharField(max_length=128, blank=True)
    rpc_password = models.CharField(max_length=256, blank=True)
    headers = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover - admin display
        return f"Node<{self.currency.code}>"


class WalletAccount(models.Model):
    """User wallet balance per currency."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet_accounts")
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="accounts")
    balance = models.DecimalField(max_digits=24, decimal_places=10, default=Decimal("0"))
    available_balance = models.DecimalField(max_digits=24, decimal_places=10, default=Decimal("0"))
    address_index = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "currency")

    def __str__(self):  # pragma: no cover - admin display
        return f"Wallet<{self.user}:{self.currency.code}>"

    def credit(self, amount: Decimal, reference: str, metadata: dict | None = None) -> "WalletTransaction":
        return WalletTransaction.record(
            account=self,
            amount=amount,
            direction=WalletTransaction.Direction.CREDIT,
            reference=reference,
            metadata=metadata or {},
        )

    def debit(self, amount: Decimal, reference: str, metadata: dict | None = None) -> "WalletTransaction":
        return WalletTransaction.record(
            account=self,
            amount=amount,
            direction=WalletTransaction.Direction.DEBIT,
            reference=reference,
            metadata=metadata or {},
        )


class DepositAddress(models.Model):
    """Deposit addresses bound to a wallet account."""

    account = models.ForeignKey(WalletAccount, on_delete=models.CASCADE, related_name="deposit_addresses")
    address = models.CharField(max_length=256)
    label = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("account", "address")

    def __str__(self):  # pragma: no cover - admin display
        return f"{self.account.currency.code}:{self.address[:10]}"


class WalletTransaction(models.Model):
    """Ledger of wallet movements."""

    class Direction(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    account = models.ForeignKey(WalletAccount, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=24, decimal_places=10)
    direction = models.CharField(max_length=16, choices=Direction.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=128, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def record(
        cls,
        account: WalletAccount,
        amount: Decimal,
        direction: str,
        reference: str = "",
        metadata: dict | None = None,
        status: str = Status.CONFIRMED,
    ) -> "WalletTransaction":
        if amount <= 0:
            raise ValueError("Amount must be positive")

        metadata = metadata or {}

        with transaction.atomic():
            wallet = WalletAccount.objects.select_for_update().get(pk=account.pk)
            if direction == cls.Direction.DEBIT and wallet.available_balance < amount:
                raise ValueError("Insufficient available balance")

            if direction == cls.Direction.CREDIT:
                wallet.balance += amount
                wallet.available_balance += amount
            else:
                wallet.balance -= amount
                wallet.available_balance -= amount

            wallet.save(update_fields=["balance", "available_balance", "updated_at"])

            tx = cls.objects.create(
                account=wallet,
                amount=amount,
                direction=direction,
                status=status,
                reference=reference,
                metadata=metadata,
            )
        return tx


class WalletBalanceSnapshot(models.Model):
    """Historical balance snapshots for analytics."""

    account = models.ForeignKey(WalletAccount, on_delete=models.CASCADE, related_name="snapshots")
    balance = models.DecimalField(max_digits=24, decimal_places=10)
    available_balance = models.DecimalField(max_digits=24, decimal_places=10)
    captured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-captured_at"]

