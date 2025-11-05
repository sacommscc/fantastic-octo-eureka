"""Views for notifications module."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from .forms import NotificationPreferencesForm
from .models import NotificationLog


class NotificationPreferencesView(LoginRequiredMixin, FormView):
    template_name = "notifications/preferences.html"
    success_url = reverse_lazy("notifications:preferences")
    form_class = NotificationPreferencesForm

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        if self.request.method == "GET":
            kwargs["data"] = None
        return kwargs

    def form_valid(self, form):  # type: ignore[override]
        form.save()
        messages.success(self.request, "Notification preferences updated.")
        return super().form_valid(form)


class NotificationLogListView(LoginRequiredMixin, ListView):
    template_name = "notifications/logs.html"
    paginate_by = 25
    model = NotificationLog

    def get_queryset(self):  # type: ignore[override]
        return self.request.user.notification_logs.select_related("template")

