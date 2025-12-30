from dj_rest_auth.views import LoginView as DjRestAuthLoginView
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.core.email import send_email
from backend.apps.users.serializers import (
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
