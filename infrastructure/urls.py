from __future__ import annotations

from django.urls import path

from . import views

app_name = "infrastructure"

urlpatterns = [
    path("", views.InfrastructureDashboardView.as_view(), name="dashboard"),
    path("service/update/", views.ServiceStatusCreateView.as_view(), name="service_update"),
    path("backup/log/", views.BackupLogCreateView.as_view(), name="backup_log"),
]
