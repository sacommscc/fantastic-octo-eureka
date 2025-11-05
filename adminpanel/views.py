"""Administrative console views."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView, TemplateView, UpdateView
from django.views.generic.edit import FormMixin

from analytics.services import membership_summary, support_summary, wallet_summary
from memberships.models import MembershipGroup, MembershipPlan
from notifications.models import NotificationTemplate
from wallets.models import Currency, NodeConfiguration

from .forms import (
    CurrencyForm,
    MembershipGroupForm,
    MembershipPlanForm,
    NodeConfigurationForm,
    NotificationTemplateForm,
)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):  # type: ignore[override]
        return self.request.user.is_staff

    def handle_no_permission(self):  # type: ignore[override]
        messages.error(self.request, "Administrator access required.")
        return super().handle_no_permission()


class AdminDashboardView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/dashboard.html"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "membership_summary": membership_summary(),
                "wallet_summary": wallet_summary(),
                "support_summary": list(support_summary()),
            }
        )
        context["currencies"] = Currency.objects.all()
        context["node_configs"] = NodeConfiguration.objects.select_related("currency")
        context["notification_templates"] = NotificationTemplate.objects.count()
        return context


class CurrencyManageView(LoginRequiredMixin, StaffRequiredMixin, FormMixin, ListView):
    template_name = "adminpanel/currency_manage.html"
    model = Currency
    form_class = CurrencyForm
    success_url = reverse_lazy("adminpanel:currencies")

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        if self.request.method == "POST":
            kwargs.update({"data": self.request.POST})
        return kwargs

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        form = self.get_form()
        if form.is_valid():
            form.save()
            messages.success(request, "Currency saved.")
            return self.form_valid(form)
        return self.form_invalid(form)


class NodeConfigurationUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    template_name = "adminpanel/node_form.html"
    model = NodeConfiguration
    form_class = NodeConfigurationForm
    success_url = reverse_lazy("adminpanel:dashboard")

    def form_valid(self, form):  # type: ignore[override]
        messages.success(self.request, "Node configuration updated.")
        return super().form_valid(form)


class NotificationTemplateManageView(LoginRequiredMixin, StaffRequiredMixin, FormMixin, ListView):
    template_name = "adminpanel/notification_templates.html"
    model = NotificationTemplate
    form_class = NotificationTemplateForm
    success_url = reverse_lazy("adminpanel:notification_templates")

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        if self.request.method == "POST":
            kwargs.update({"data": self.request.POST})
        return kwargs

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        form = self.get_form()
        if form.is_valid():
            form.save()
            messages.success(request, "Template saved.")
            return self.form_valid(form)
        return self.form_invalid(form)


class MembershipGroupManageView(LoginRequiredMixin, StaffRequiredMixin, FormMixin, ListView):
    template_name = "adminpanel/group_manage.html"
    model = MembershipGroup
    form_class = MembershipGroupForm
    success_url = reverse_lazy("adminpanel:groups")

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        if self.request.method == "POST":
            kwargs.update({"data": self.request.POST})
        return kwargs

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        form = self.get_form()
        if form.is_valid():
            form.save()
            messages.success(request, "Membership group saved.")
            return self.form_valid(form)
        return self.form_invalid(form)


class MembershipPlanManageView(LoginRequiredMixin, StaffRequiredMixin, FormMixin, ListView):
    template_name = "adminpanel/plan_manage.html"
    model = MembershipPlan
    form_class = MembershipPlanForm
    success_url = reverse_lazy("adminpanel:plans")

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        if self.request.method == "POST":
            kwargs.update({"data": self.request.POST})
        return kwargs

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        form = self.get_form()
        if form.is_valid():
            plan = form.save()
            messages.success(request, f"Plan saved for group {plan.group.name}.")
            return self.form_valid(form)
        return self.form_invalid(form)

