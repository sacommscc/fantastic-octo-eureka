"""Infrastructure status views."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from .forms import BackupLogForm, ServiceStatusForm
from .models import BackupLog, ServiceStatus, SystemMetric


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):  # type: ignore[override]
        return self.request.user.is_staff

    def handle_no_permission(self):  # type: ignore[override]
        messages.error(self.request, "Administrator access required.")
        return super().handle_no_permission()


class InfrastructureDashboardView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    template_name = "infrastructure/dashboard.html"
    model = ServiceStatus
    context_object_name = "services"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["metrics"] = SystemMetric.objects.all()[:10]
        context["backup_logs"] = BackupLog.objects.all()[:10]
        context["service_form"] = ServiceStatusForm()
        context["backup_form"] = BackupLogForm()
        return context


class ServiceStatusCreateView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    form_class = ServiceStatusForm
    success_url = reverse_lazy("infrastructure:dashboard")

    def form_valid(self, form):  # type: ignore[override]
        ServiceStatus.objects.update_or_create(name=form.cleaned_data["name"], defaults=form.cleaned_data)
        messages.success(self.request, "Service status updated.")
        return super().form_valid(form)


class BackupLogCreateView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    form_class = BackupLogForm
    success_url = reverse_lazy("infrastructure:dashboard")

    def form_valid(self, form):  # type: ignore[override]
        form.save()
        messages.success(self.request, "Backup log recorded.")
        return super().form_valid(form)

