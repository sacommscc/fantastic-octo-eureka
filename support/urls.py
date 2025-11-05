from __future__ import annotations

from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("", views.SupportTicketListView.as_view(), name="tickets"),
    path("create/", views.SupportTicketCreateView.as_view(), name="ticket_create"),
    path("<int:pk>/", views.SupportTicketDetailView.as_view(), name="ticket_detail"),
    path("admin/", views.SupportTicketAdminListView.as_view(), name="admin_tickets"),
]
