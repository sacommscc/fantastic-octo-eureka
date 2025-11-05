from __future__ import annotations

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("recovery/", views.MnemonicRecoveryView.as_view(), name="recovery"),
    path("recovery/verify/", views.OTPVerificationView.as_view(), name="verify_otp"),
    path("sessions/", views.SessionListView.as_view(), name="sessions"),
    path("sessions/<str:session_key>/terminate/", views.TerminateSessionView.as_view(), name="terminate_session"),
]
