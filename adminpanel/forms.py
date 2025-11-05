"""Forms for administrative configuration."""

from __future__ import annotations

from django import forms

from memberships.models import MembershipGroup, MembershipPlan
from notifications.models import NotificationTemplate
from wallets.models import Currency, NodeConfiguration


class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ("code", "name", "symbol", "network", "precision", "is_crypto", "is_active")


class NodeConfigurationForm(forms.ModelForm):
    class Meta:
        model = NodeConfiguration
        fields = (
            "rpc_url",
            "rpc_username",
            "rpc_password",
            "headers",
            "is_active",
        )


class NotificationTemplateForm(forms.ModelForm):
    class Meta:
        model = NotificationTemplate
        fields = ("code", "channel", "subject", "body", "is_active")


class MembershipGroupForm(forms.ModelForm):
    class Meta:
        model = MembershipGroup
        fields = ("name", "slug", "description", "level", "is_active", "color")


class MembershipPlanForm(forms.ModelForm):
    class Meta:
        model = MembershipPlan
        fields = (
            "group",
            "name",
            "currency",
            "amount",
            "interval",
            "duration_days",
            "is_active",
            "allow_upgrade_to",
        )
        widgets = {"allow_upgrade_to": forms.CheckboxSelectMultiple}

