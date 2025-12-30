import random
import string

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Email verification fields
    is_email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    email_verification_code_created_at = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    # Verification code expires after 15 minutes
    VERIFICATION_CODE_EXPIRY_MINUTES = 15

    def __str__(self):
        return self.email

    def generate_verification_code(self):
        """Generate a 6-digit verification code and set the timestamp."""
        self.email_verification_code = "".join(random.choices(string.digits, k=6))
        self.email_verification_code_created_at = timezone.now()
        self.save(update_fields=["email_verification_code", "email_verification_code_created_at"])
        return self.email_verification_code

    def is_verification_code_valid(self, code):
        """Check if the provided code matches and hasn't expired."""
        if not self.email_verification_code or not self.email_verification_code_created_at:
            return False
        if self.email_verification_code != code:
            return False
        expiry_time = self.email_verification_code_created_at + timezone.timedelta(
            minutes=self.VERIFICATION_CODE_EXPIRY_MINUTES
        )
        return timezone.now() <= expiry_time

    def verify_email(self):
        """Mark the email as verified and clear the verification code."""
        self.is_email_verified = True
        self.email_verification_code = None
        self.email_verification_code_created_at = None
        self.save(update_fields=[
            "is_email_verified",
            "email_verification_code",
            "email_verification_code_created_at",
        ])
