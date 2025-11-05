"""Forms for memberships interactions."""

from __future__ import annotations

from django import forms

from wallets.models import WalletAccount


class MembershipPurchaseForm(forms.Form):
    wallet_account = forms.ModelChoiceField(queryset=WalletAccount.objects.none())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.plan = kwargs.pop("plan")
        super().__init__(*args, **kwargs)
        qs = self.user.wallet_accounts.filter(currency=self.plan.currency)
        self.fields["wallet_account"].queryset = qs
        self.fields["wallet_account"].label = f"Pay with {self.plan.currency.code} wallet"

        if not qs.exists():
            self.fields["wallet_account"].help_text = "No wallet found for this currency. Configure one in your wallet settings."


class MembershipUpgradeForm(forms.Form):
    wallet_account = forms.ModelChoiceField(queryset=WalletAccount.objects.none())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.current_membership = kwargs.pop("membership")
        self.target_plan = kwargs.pop("target_plan")
        self.additional_cost = kwargs.pop("additional_cost")
        super().__init__(*args, **kwargs)
        qs = self.user.wallet_accounts.filter(currency=self.target_plan.currency)
        self.fields["wallet_account"].queryset = qs
        self.fields["wallet_account"].label = f"Pay upgrade cost ({self.additional_cost} {self.target_plan.currency.code})"

