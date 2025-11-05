"""Forms for wallet interactions."""

from __future__ import annotations

from decimal import Decimal

from django import forms

from .models import Currency, WalletAccount


class WalletCreateForm(forms.Form):
    currency = forms.ModelChoiceField(queryset=Currency.objects.filter(is_active=True))


class DepositAddressForm(forms.Form):
    wallet_account = forms.ModelChoiceField(queryset=WalletAccount.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["wallet_account"].queryset = user.wallet_accounts.select_related("currency")


class WithdrawalForm(forms.Form):
    wallet_account = forms.ModelChoiceField(queryset=WalletAccount.objects.none())
    amount = forms.DecimalField(min_value=Decimal("0.00000001"), max_digits=18, decimal_places=8)
    address = forms.CharField(max_length=255)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["wallet_account"].queryset = self.user.wallet_accounts.select_related("currency")

    def clean(self):  # type: ignore[override]
        data = super().clean()
        account: WalletAccount = data.get("wallet_account")
        amount = data.get("amount")
        if account and amount and account.available_balance < amount:
            self.add_error("amount", "Insufficient balance.")
        return data

