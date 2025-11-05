"""Views for the accounts domain."""

from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, UpdateView, View

from .forms import LoginForm, MnemonicResetForm, ProfileUpdateForm, RegistrationForm
from .models import ActiveSession, RecoverySession, User
from .services import RecoveryOrchestrator, generate_mnemonic_phrase


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = RegistrationForm

    def form_valid(self, form: RegistrationForm) -> HttpResponse:
        mnemonic = generate_mnemonic_phrase()
        user: User = form.save(commit=False)
        user.set_mnemonic_phrase(mnemonic)
        user.save()
        form.save_m2m()

        login(self.request, user)

        messages.success(self.request, "Account created. Store your recovery phrase securely.")
        return render(
            self.request,
            "accounts/register_success.html",
            {
                "mnemonic_phrase": mnemonic,
            },
        )


class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy("accounts:login")


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = "accounts/profile.html"
    form_class = ProfileUpdateForm
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):  # type: ignore[override]
        return self.request.user

    def form_valid(self, form):  # type: ignore[override]
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)


class MnemonicRecoveryView(FormView):
    template_name = "accounts/recovery.html"
    form_class = MnemonicResetForm
    success_url = reverse_lazy("accounts:login")
    orchestrator_class = RecoveryOrchestrator

    def form_valid(self, form: MnemonicResetForm) -> HttpResponse:
        username = form.cleaned_data["username"]
        phrase = form.cleaned_data["mnemonic_phrase"]

        try:
            user = User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            messages.error(self.request, "Invalid recovery information.")
            return self.form_invalid(form)

        if not user.can_attempt_recovery():
            messages.error(self.request, "Recovery temporarily locked. Try again later.")
            return self.form_invalid(form)

        if not user.check_mnemonic_phrase(phrase):
            user.register_recovery_attempt(success=False)
            messages.error(self.request, "Mnemonic phrase mismatch.")
            return self.form_invalid(form)

        orchestrator = self.orchestrator_class()
        challenge = orchestrator.initiate_session(user)
        challenge.recovery_session.mnemonic_confirmed = True
        challenge.recovery_session.save(update_fields=["mnemonic_confirmed"])
        request = self.request
        request.session["recovery_session_id"] = challenge.recovery_session.pk
        request.session["recovery_otp"] = challenge.otp_code
        request.session["recovery_user_id"] = user.pk
        request.session.set_expiry(15 * 60)

        user.register_recovery_attempt(success=True)
        messages.info(request, "OTP sent via your preferred channel.")

        return redirect("accounts:verify_otp")


class SessionListView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/sessions.html"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["sessions"] = self.request.user.sessions.filter(is_active=True)
        return context


class TerminateSessionView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request: HttpRequest, session_key: str) -> HttpResponse:
        try:
            session = request.user.sessions.get(session_key=session_key)
        except ActiveSession.DoesNotExist as exc:  # pragma: no cover - guard
            raise Http404 from exc

        session.terminate()
        messages.success(request, "Session marked for termination.")
        return redirect("accounts:sessions")


class OTPVerificationView(FormView):
    template_name = "accounts/verify_otp.html"
    success_url = reverse_lazy("accounts:login")

    class OTPForm(forms.Form):
        otp_code = forms.CharField(min_length=6, max_length=6)
        new_password1 = forms.CharField(widget=forms.PasswordInput)
        new_password2 = forms.CharField(widget=forms.PasswordInput)

        def clean(self):  # type: ignore[override]
            data = super().clean()
            if data.get("new_password1") != data.get("new_password2"):
                self.add_error("new_password2", "Passwords do not match.")
            return data

    form_class = OTPForm

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        if not request.session.get("recovery_session_id"):
            return redirect("accounts:recovery")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):  # type: ignore[override]
        session_id = self.request.session.get("recovery_session_id")
        user_id = self.request.session.get("recovery_user_id")
        otp_expected = self.request.session.get("recovery_otp")
        otp_submitted = form.cleaned_data["otp_code"]

        if otp_expected != otp_submitted:
            messages.error(self.request, "Incorrect OTP. Try again.")
            return self.form_invalid(form)

        try:
            recovery_session = RecoverySession.objects.get(pk=session_id)
        except RecoverySession.DoesNotExist as exc:  # pragma: no cover - guard
            raise Http404 from exc

        if not recovery_session.is_active():
            messages.error(self.request, "Recovery session expired.")
            return redirect("accounts:recovery")

        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist as exc:  # pragma: no cover - guard
            raise Http404 from exc

        user.set_password(form.cleaned_data["new_password1"])
        user.save(update_fields=["password"])

        recovery_session.mnemonic_confirmed = True
        recovery_session.otp_confirmed = True
        recovery_session.save(update_fields=["mnemonic_confirmed", "otp_confirmed"])
        recovery_session.mark_verified()

        for key in ["recovery_session_id", "recovery_otp", "recovery_user_id"]:
            if key in self.request.session:
                del self.request.session[key]

        messages.success(self.request, "Password reset successfully. You may now log in.")
        return super().form_valid(form)
