from __future__ import annotations

from django.urls import path

from . import views

app_name = "wallets"

urlpatterns = [
    path("", views.WalletListView.as_view(), name="list"),
    path("create/", views.WalletCreateView.as_view(), name="create"),
    path("deposit/", views.DepositAddressView.as_view(), name="deposit"),
    path("withdraw/", views.WithdrawalView.as_view(), name="withdraw"),
]
