"""Forms for support module."""

from __future__ import annotations

from django import forms

from .models import SupportTicket, TicketMessage


class SupportTicketForm(forms.ModelForm):
    initial_message = forms.CharField(widget=forms.Textarea, label="Describe your issue")

    class Meta:
        model = SupportTicket
        fields = ("subject", "category", "priority")


class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3}),
        }

