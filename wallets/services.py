"""Wallet service layer and node integrations."""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

import requests
from django.utils import timezone

from .models import Currency, DepositAddress, NodeConfiguration, WalletAccount, WalletTransaction


logger = logging.getLogger(__name__)


class NodeClientError(RuntimeError):
    pass


class CryptoNodeClient(abc.ABC):
    """Abstract node client interface."""

    def __init__(self, node: NodeConfiguration):
        self.node = node

    @abc.abstractmethod
    def generate_address(self, account: WalletAccount) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_balance(self) -> Decimal:
        raise NotImplementedError

    @abc.abstractmethod
    def list_transactions(self) -> Iterable[dict]:
        raise NotImplementedError


class JsonRpcClient(CryptoNodeClient):
    """Generic JSON-RPC client for BTC-like nodes."""

    def _post(self, method: str, params: list | None = None) -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        auth = None
        if self.node.rpc_username:
            auth = (self.node.rpc_username, self.node.rpc_password)

        response = requests.post(
            self.node.rpc_url,
            json=payload,
            headers=self.node.headers or {},
            auth=auth,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data and data["error"]:
            raise NodeClientError(str(data["error"]))
        return data["result"]

    def generate_address(self, account: WalletAccount) -> str:
        label = f"user_{account.user_id}"
        return self._post("getnewaddress", [label])

    def get_balance(self) -> Decimal:
        return Decimal(str(self._post("getbalance")))

    def list_transactions(self) -> Iterable[dict]:
        return self._post("listtransactions", ["*", 100])


class PlaceholderNodeClient(CryptoNodeClient):
    """Fallback implementation storing operations in logs."""

    def generate_address(self, account: WalletAccount) -> str:
        fake_address = f"{account.currency.code}_ADDR_{timezone.now().timestamp():.0f}_{account.pk}"
        logger.warning("Using placeholder address generation for %s", account.currency.code)
        return fake_address

    def get_balance(self) -> Decimal:
        return Decimal("0")

    def list_transactions(self) -> Iterable[dict]:
        return []


def get_node_client(currency: Currency) -> CryptoNodeClient:
    try:
        node = currency.node
    except NodeConfiguration.DoesNotExist as exc:  # pragma: no cover - guard
        raise NodeClientError(f"No node configured for {currency.code}") from exc

    if currency.code in {"BTC", "XMR", "USDT"}:
        return JsonRpcClient(node)
    return PlaceholderNodeClient(node)


@dataclass
class WalletService:
    """High-level operations for wallet accounts."""

    def ensure_account(self, user, currency: Currency) -> WalletAccount:
        account, _ = WalletAccount.objects.get_or_create(user=user, currency=currency)
        return account

    def generate_deposit_address(self, account: WalletAccount) -> DepositAddress:
        client = get_node_client(account.currency)
        address = client.generate_address(account)
        deposit_address, _ = DepositAddress.objects.get_or_create(
            account=account,
            address=address,
            defaults={"label": f"{account.currency.code} deposit"},
        )
        return deposit_address

    def record_deposit(self, account: WalletAccount, amount: Decimal, txid: str) -> WalletTransaction:
        return account.credit(amount, reference=txid, metadata={"type": "deposit"})

    def request_withdrawal(self, account: WalletAccount, amount: Decimal, target_address: str) -> WalletTransaction:
        tx = account.debit(amount, reference=f"withdrawal:{target_address}", metadata={"type": "withdrawal"})
        return tx

