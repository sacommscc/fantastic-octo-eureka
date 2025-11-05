"""Views for wallet operations."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from .forms import DepositAddressForm, WalletCreateForm, WithdrawalForm
from .models import WalletAccount
from .services import WalletService


class WalletListView(LoginRequiredMixin, ListView):
    template_name = "wallets/wallet_list.html"
    model = WalletAccount

    def get_queryset(self):  # type: ignore[override]
        return self.request.user.wallet_accounts.select_related("currency").all()


class WalletCreateView(LoginRequiredMixin, FormView):
    template_name = "wallets/wallet_create.html"
    form_class = WalletCreateForm
    success_url = reverse_lazy("wallets:list")

    def form_valid(self, form):  # type: ignore[override]
        service = WalletService()
        currency = form.cleaned_data["currency"]
        service.ensure_account(self.request.user, currency)
        messages.success(self.request, f"Wallet for {currency.code} ready.")
        return super().form_valid(form)


class DepositAddressView(LoginRequiredMixin, FormView):
    template_name = "wallets/deposit_address.html"
    form_class = DepositAddressForm
    success_url = reverse_lazy("wallets:list")

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):  # type: ignore[override]
        account = form.cleaned_data["wallet_account"]
        try:
            deposit_address = WalletService().generate_deposit_address(account)
        except Exception as exc:  # pragma: no cover - runtime guard
            messages.error(self.request, f"Could not generate address: {exc}")
            return self.form_invalid(form)
        messages.success(self.request, f"New deposit address generated: {deposit_address.address}")
        return super().form_valid(form)


class WithdrawalView(LoginRequiredMixin, FormView):
    template_name = "wallets/withdraw.html"
    form_class = WithdrawalForm
    success_url = reverse_lazy("wallets:list")

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):  # type: ignore[override]
        account = form.cleaned_data["wallet_account"]
        amount = form.cleaned_data["amount"]
        address = form.cleaned_data["address"]
        try:
            WalletService().request_withdrawal(account, amount, address)
        except Exception as exc:  # pragma: no cover - runtime guard
            messages.error(self.request, f"Withdrawal failed: {exc}")
            return self.form_invalid(form)
        messages.success(self.request, "Withdrawal queued for processing.")
        return super().form_valid(form)

