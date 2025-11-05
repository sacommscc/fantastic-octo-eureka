"""Analytics dashboard views."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView

from .services import membership_summary, support_summary, wallet_summary


class AnalyticsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "analytics/dashboard.html"

    def test_func(self):  # type: ignore[override]
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "membership_summary": membership_summary(),
                "wallet_summary": wallet_summary(),
                "support_summary": list(support_summary()),
            }
        )
        return context

