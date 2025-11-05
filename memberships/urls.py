from __future__ import annotations

from django.urls import path

from . import views

app_name = "memberships"

urlpatterns = [
    path("", views.MembershipCatalogView.as_view(), name="catalog"),
    path("plan/<int:pk>/", views.MembershipPlanDetailView.as_view(), name="plan_detail"),
    path("plan/<int:pk>/purchase/", views.MembershipPurchaseView.as_view(), name="purchase"),
    path("plan/<int:pk>/upgrade/", views.MembershipUpgradeView.as_view(), name="upgrade"),
]
