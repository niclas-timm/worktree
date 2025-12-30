from django.urls import path

from backend.apps.users.views import LoginView, ResendVerificationView, VerifyEmailView

urlpatterns = [
    path("login/", LoginView.as_view(), name="rest_login"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend_verification"),
]
