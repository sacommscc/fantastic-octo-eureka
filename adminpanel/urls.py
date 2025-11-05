from __future__ import annotations

from django.urls import path

from . import views

app_name = "adminpanel"

urlpatterns = [
    path("", views.AdminDashboardView.as_view(), name="dashboard"),
    path("currencies/", views.CurrencyManageView.as_view(), name="currencies"),
    path("nodes/<int:pk>/", views.NodeConfigurationUpdateView.as_view(), name="node_edit"),
    path("notifications/", views.NotificationTemplateManageView.as_view(), name="notification_templates"),
    path("groups/", views.MembershipGroupManageView.as_view(), name="groups"),
    path("plans/", views.MembershipPlanManageView.as_view(), name="plans"),
]
