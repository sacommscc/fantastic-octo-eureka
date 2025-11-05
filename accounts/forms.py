"""Forms for the accounts application."""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User, mnemonic_validator


class RegistrationForm(UserCreationForm):
    preferred_channel = forms.ChoiceField(
        choices=User.NotificationChannel.choices,
        widget=forms.RadioSelect,
        initial=User.NotificationChannel.TELEGRAM,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "preferred_channel",
            "xmpp_address",
            "telegram_username",
            "password1",
            "password2",
        )

    def clean(self):  # type: ignore[override]
        data = super().clean()
        channel = data.get("preferred_channel")
        if channel == User.NotificationChannel.JABBER and not data.get("xmpp_address"):
            self.add_error("xmpp_address", "Jabber/XMPP address is required for this channel.")
        if channel == User.NotificationChannel.TELEGRAM and not data.get("telegram_username"):
            self.add_error("telegram_username", "Telegram username is required for this channel.")
        return data


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"autofocus": True}))


class MnemonicResetForm(forms.Form):
    username = forms.CharField(max_length=150)
    mnemonic_phrase = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

    def clean_mnemonic_phrase(self):
        phrase = self.cleaned_data.get("mnemonic_phrase", "").strip()
        mnemonic_validator(phrase)
        return phrase


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "preferred_channel",
            "xmpp_address",
            "telegram_username",
            "requires_mfa",
        )

