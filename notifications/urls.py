from __future__ import annotations

from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("preferences/", views.NotificationPreferencesView.as_view(), name="preferences"),
    path("logs/", views.NotificationLogListView.as_view(), name="logs"),
]
