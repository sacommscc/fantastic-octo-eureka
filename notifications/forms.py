"""Forms for notification settings."""

from __future__ import annotations

from django import forms

from .models import NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ("enabled",)


class NotificationPreferencesForm(forms.Form):
    """Aggregate form for all channels."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        for preference in self.user.notification_preferences.all():
            field_name = f"channel_{preference.channel}"
            self.fields[field_name] = forms.BooleanField(
                label=preference.get_channel_display(),
                required=False,
                initial=preference.enabled,
            )

    def save(self):
        for preference in self.user.notification_preferences.all():
            field_name = f"channel_{preference.channel}"
            preference.enabled = self.cleaned_data.get(field_name, False)
            preference.save(update_fields=["enabled", "updated_at"])

