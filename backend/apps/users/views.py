from dj_rest_auth.views import LoginView as DjRestAuthLoginView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.core.email import send_email
from backend.apps.users.serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    ResendVerificationSerializer,
    VerifyEmailSerializer,
)

User = get_user_model()


class LoginView(DjRestAuthLoginView):
    """Custom login view that checks email verification status."""

    def post(self, request, *args, **kwargs):
        # First, validate credentials using parent's serializer
        self.request = request
        self.serializer = self.get_serializer(data=request.data)

        try:
            self.serializer.is_valid(raise_exception=True)
        except Exception:
            # Let the parent handle invalid credentials
            return super().post(request, *args, **kwargs)

        # Get the user from the validated serializer
        user = self.serializer.validated_data.get("user")

        # Check if email is verified
        if user and not user.is_email_verified:
            return Response(
                {
                    "email_not_verified": True,
                    "email": user.email,
                    "detail": "Please verify your email before logging in.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Proceed with normal login
        return super().post(request, *args, **kwargs)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_email_verified:
            return Response(
                {"detail": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_verification_code_valid(code):
            return Response(
                {"detail": "Invalid or expired verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.verify_email()

        # Create or get auth token for automatic login
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "detail": "Email verified successfully.",
                "key": token.key,
            },
            status=status.HTTP_200_OK,
        )


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return success even if user doesn't exist (security: don't reveal user existence)
            return Response(
                {"detail": "If an account exists with this email, a verification code has been sent."},
                status=status.HTTP_200_OK,
            )

        if user.is_email_verified:
            return Response(
                {"detail": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate new code and send email
        code = user.generate_verification_code()
        send_email(
            to=user.email,
            subject="Verify your email address",
            template_name="auth/verify_email",
            context={
                "name": user.name,
                "verification_code": code,
            },
        )

        return Response(
            {"detail": "Verification code sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetView(APIView):
    """Request a password reset email."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return success even if user doesn't exist (security: don't reveal user existence)
            return Response(
                {"detail": "If an account exists with this email, a password reset link has been sent."},
                status=status.HTTP_200_OK,
            )

        # Generate password reset token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Build reset URL pointing to frontend
        reset_url = f"{settings.SITE_URL}/reset-password/{uid}/{token}"

        send_email(
            to=user.email,
            subject="Reset your password",
            template_name="auth/password_reset",
            context={
                "user": user,
                "password_reset_url": reset_url,
            },
        )

        return Response(
            {"detail": "If an account exists with this email, a password reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token and set new password."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired password reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired password reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )
