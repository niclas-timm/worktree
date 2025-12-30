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
        user = super().save(request)
        user.name = self.validated_data.get("name", "")
        user.save()
        return user
