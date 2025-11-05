"""Celery tasks for wallet operations."""

from __future__ import annotations

from decimal import Decimal

from celery import shared_task

from .models import Currency, WalletAccount
from .services import WalletService, get_node_client


@shared_task(name="wallets.poll_transactions")
def poll_transactions():  # pragma: no cover - scheduled task
    for currency in Currency.objects.filter(is_active=True):
        try:
            client = get_node_client(currency)
        except Exception:
            continue

        for tx in client.list_transactions():
            if tx.get("category") not in {"receive"}:
                continue
            address = tx.get("address")
            amount = Decimal(str(tx.get("amount", 0)))
            txid = tx.get("txid") or tx.get("id")
            if not address or not txid or amount <= 0:
                continue

            for account in WalletAccount.objects.filter(deposit_addresses__address=address).distinct():
                WalletService().record_deposit(account, amount, txid)

