"""Views for support tickets."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.edit import FormMixin

from .forms import SupportTicketForm, TicketReplyForm
from .models import SupportTicket, TicketMessage


class SupportTicketListView(LoginRequiredMixin, ListView):
    template_name = "support/ticket_list.html"
    paginate_by = 20
    model = SupportTicket

    def get_queryset(self):  # type: ignore[override]
        return self.request.user.tickets.select_related("category").all()


class SupportTicketCreateView(LoginRequiredMixin, FormView):
    template_name = "support/ticket_create.html"
    form_class = SupportTicketForm
    success_url = reverse_lazy("support:tickets")

    def form_valid(self, form):  # type: ignore[override]
        ticket = form.save(commit=False)
        ticket.user = self.request.user
        ticket.save()
        TicketMessage.objects.create(ticket=ticket, author=self.request.user, body=form.cleaned_data["initial_message"])
        messages.success(self.request, "Support ticket created.")
        return super().form_valid(form)


class SupportTicketDetailView(LoginRequiredMixin, FormMixin, DetailView):
    template_name = "support/ticket_detail.html"
    model = SupportTicket
    form_class = TicketReplyForm
    context_object_name = "ticket"
    success_url = None

    def get_object(self, queryset=None):  # type: ignore[override]
        ticket = super().get_object(queryset)
        if ticket.user != self.request.user and not self.request.user.is_staff:
            raise PermissionError
        return ticket

    def get_success_url(self):  # type: ignore[override]
        return reverse_lazy("support:ticket_detail", kwargs={"pk": self.get_object().pk})

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):  # type: ignore[override]
        ticket = self.get_object()
        message = form.save(commit=False)
        message.ticket = ticket
        message.author = self.request.user
        message.save()
        messages.success(self.request, "Reply submitted.")
        return redirect("support:ticket_detail", pk=ticket.pk)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["ticket_messages"] = self.get_object().messages.select_related("author")
        return context


class SupportTicketAdminListView(UserPassesTestMixin, ListView):
    template_name = "support/admin_ticket_list.html"
    model = SupportTicket
    paginate_by = 30

    def test_func(self):  # type: ignore[override]
        return self.request.user.is_staff

    def handle_no_permission(self):  # type: ignore[override]
        messages.error(self.request, "Administrator access required.")
        return redirect("support:tickets")

    def get_queryset(self):  # type: ignore[override]
        return SupportTicket.objects.select_related("user", "category").all()

