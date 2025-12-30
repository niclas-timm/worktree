from django.urls import path

from backend.apps.users.views import (
    CompleteOnboardingView,
    LoginView,
    PasswordResetConfirmView,
    PasswordResetView,
    ResendVerificationView,
    VerifyEmailView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="rest_login"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend_verification"),
    path("password/reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("complete-onboarding/", CompleteOnboardingView.as_view(), name="complete_onboarding"),
]
