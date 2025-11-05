"""Views for memberships."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView

from .forms import MembershipPurchaseForm, MembershipUpgradeForm
from .models import MembershipPlan, MembershipUpgradeRule, UserMembership
from .services import MembershipService


class MembershipCatalogView(ListView):
    template_name = "memberships/catalog.html"
    model = MembershipPlan

    def get_queryset(self):  # type: ignore[override]
        return (
            MembershipPlan.objects.filter(is_active=True)
            .select_related("group", "currency")
            .order_by("group__level", "amount")
        )


class MembershipPlanDetailView(DetailView):
    template_name = "memberships/plan_detail.html"
    model = MembershipPlan
    context_object_name = "plan"


class MembershipPurchaseView(LoginRequiredMixin, FormView):
    template_name = "memberships/purchase.html"
    form_class = MembershipPurchaseForm
    success_url = reverse_lazy("memberships:catalog")
    service_class = MembershipService

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        self.plan = get_object_or_404(
            MembershipPlan.objects.select_related("group", "currency"), pk=kwargs.get("pk"), is_active=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        kwargs.update({"user": self.request.user, "plan": self.plan})
        return kwargs

    def form_valid(self, form):  # type: ignore[override]
        wallet_account = form.cleaned_data["wallet_account"]
        service = self.service_class()
        try:
            membership = service.purchase_plan(self.request.user, self.plan, wallet_account)
        except Exception as exc:  # pragma: no cover - handles runtime issues
            messages.error(self.request, f"Unable to process membership: {exc}")
            return self.form_invalid(form)

        messages.success(self.request, f"Membership activated: {membership.plan.name}")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["plan"] = self.plan
        return context


class MembershipUpgradeView(LoginRequiredMixin, FormView):
    template_name = "memberships/upgrade.html"
    form_class = MembershipUpgradeForm
    success_url = reverse_lazy("memberships:catalog")
    service_class = MembershipService

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        self.target_plan = get_object_or_404(MembershipPlan, pk=kwargs.get("pk"), is_active=True)
        self.current_membership = (
            UserMembership.objects.select_related("plan")
            .filter(user=request.user, status=UserMembership.Status.ACTIVE)
            .order_by("-expires_at")
            .first()
        )
        if not self.current_membership:
            messages.error(request, "No active membership to upgrade.")
            return redirect("memberships:catalog")
        self.rule = MembershipUpgradeRule.objects.filter(
            from_plan=self.current_membership.plan,
            to_plan=self.target_plan,
            is_active=True,
        ).first()
        if not self.rule:
            messages.error(request, "Upgrade path not available.")
            return redirect("memberships:catalog")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):  # type: ignore[override]
        kwargs = super().get_form_kwargs()
        additional_cost = self.rule.additional_cost if self.rule.additional_cost > 0 else self.target_plan.amount
        self.additional_cost = additional_cost
        kwargs.update(
            {
                "user": self.request.user,
                "membership": self.current_membership,
                "target_plan": self.target_plan,
                "additional_cost": additional_cost,
            }
        )
        return kwargs

    def form_valid(self, form):  # type: ignore[override]
        wallet_account = form.cleaned_data["wallet_account"]
        service = self.service_class()
        try:
            membership = service.upgrade_membership(self.current_membership, self.target_plan, wallet_account)
        except Exception as exc:  # pragma: no cover - runtime guard
            messages.error(self.request, f"Upgrade failed: {exc}")
            return self.form_invalid(form)

        messages.success(self.request, f"Upgraded to {membership.plan.name}")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "target_plan": self.target_plan,
                "current_membership": self.current_membership,
                "rule": self.rule,
                "additional_cost": getattr(self, "additional_cost", self.rule.additional_cost),
            }
        )
        return context

