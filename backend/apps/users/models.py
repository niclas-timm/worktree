from __future__ import annotations

import random
import string
from datetime import timedelta
from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager["User"]):
    def create_user(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> User:
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> User:
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

    # Onboarding
    is_onboarded = models.BooleanField(default=False)

    objects: UserManager = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    # Verification code expires after 15 minutes
    VERIFICATION_CODE_EXPIRY_MINUTES = 15

    def __str__(self) -> str:
        return self.email

    def generate_verification_code(self) -> str:
        """Generate a 6-digit verification code and set the timestamp."""
        self.email_verification_code = "".join(random.choices(string.digits, k=6))
        self.email_verification_code_created_at = timezone.now()
        self.save(
            update_fields=[
                "email_verification_code",
                "email_verification_code_created_at",
            ]
        )
        return self.email_verification_code

    def is_verification_code_valid(self, code: str) -> bool:
        """Check if the provided code matches and hasn't expired."""
        if (
            not self.email_verification_code
            or not self.email_verification_code_created_at
        ):
            return False
        if self.email_verification_code != code:
            return False
        expiry_time = self.email_verification_code_created_at + timedelta(
            minutes=self.VERIFICATION_CODE_EXPIRY_MINUTES
        )
        return timezone.now() <= expiry_time

    def verify_email(self) -> None:
        """Mark the email as verified and clear the verification code."""
        self.is_email_verified = True
        self.email_verification_code = None
        self.email_verification_code_created_at = None
        self.save(
            update_fields=[
                "is_email_verified",
                "email_verification_code",
                "email_verification_code_created_at",
            ]
        )
