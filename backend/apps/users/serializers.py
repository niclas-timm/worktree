from django.contrib.auth import get_user_model
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

User = get_user_model()


class CustomRegisterSerializer(RegisterSerializer):
    username = None
    name = serializers.CharField(max_length=255, required=True)
    password2 = None

    def get_cleaned_data(self):
        return {
            "email": self.validated_data.get("email", ""),
            "password1": self.validated_data.get("password1", ""),
            "name": self.validated_data.get("name", ""),
        }

    def validate_email(self, email):
        email = email.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate(self, attrs):
        if not attrs.get("email"):
            raise serializers.ValidationError({"email": "This field may not be blank."})
        if not attrs.get("password1"):
            raise serializers.ValidationError({"password1": "This field may not be blank."})
        if not attrs.get("name"):
            raise serializers.ValidationError({"name": "This field may not be blank."})
        return attrs

    def save(self, request):
        from backend.apps.core.email import send_email

        user = super().save(request)
        user.name = self.validated_data.get("name", "")
        user.save()

        # Generate verification code and send email
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

        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(max_length=6, min_length=6, required=True)

    def validate_email(self, email):
        return email.lower()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, email):
        return email.lower()
