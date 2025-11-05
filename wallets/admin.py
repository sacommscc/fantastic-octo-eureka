"""Admin registrations for wallet models."""

from __future__ import annotations

from django.contrib import admin

from .models import Currency, DepositAddress, NodeConfiguration, WalletAccount, WalletBalanceSnapshot, WalletTransaction


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "network", "precision", "is_active")
    list_filter = ("is_active", "network")
    search_fields = ("code", "name")


@admin.register(NodeConfiguration)
class NodeConfigurationAdmin(admin.ModelAdmin):
    list_display = ("currency", "rpc_url", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("currency__code", "rpc_url")


@admin.register(WalletAccount)
class WalletAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "currency", "balance", "available_balance", "created_at")
    list_filter = ("currency", "created_at")
    search_fields = ("user__username",)


@admin.register(DepositAddress)
class DepositAddressAdmin(admin.ModelAdmin):
    list_display = ("account", "address", "is_active", "created_at")
    list_filter = ("is_active", "account__currency")
    search_fields = ("address", "account__user__username")


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("account", "direction", "amount", "status", "created_at")
    list_filter = ("direction", "status", "account__currency")
    search_fields = ("account__user__username", "reference")


@admin.register(WalletBalanceSnapshot)
class WalletBalanceSnapshotAdmin(admin.ModelAdmin):
    list_display = ("account", "balance", "available_balance", "captured_at")
    list_filter = ("captured_at", "account__currency")

