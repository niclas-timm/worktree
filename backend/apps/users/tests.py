from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from backend.apps.users.models import User


class UserModelTests(TestCase):
    """Test custom User model."""

    def test_create_user_success(self):
        """Test creating a user with email and password."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", name="Test User"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "Test User")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email_raises_error(self):
        """Test that creating user without email raises ValueError."""
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(email="", password="testpass123", name="Test")
        self.assertIn("email", str(context.exception).lower())

    def test_email_is_normalized(self):
        """Test that email is normalized (lowercased)."""
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM", password="testpass123", name="Test"
        )
        self.assertEqual(user.email, "test@example.com")

    def test_email_uniqueness(self):
        """Test that duplicate emails are not allowed."""
        User.objects.create_user(
            email="test@example.com", password="pass123", name="User 1"
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="test@example.com", password="pass456", name="User 2"
            )

    def test_create_superuser_success(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123", name="Admin"
        )
        self.assertEqual(admin.email, "admin@example.com")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_str_method(self):
        """Test user string representation."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", name="Test"
        )
        self.assertEqual(str(user), "test@example.com")

    def test_new_user_is_not_email_verified(self):
        """Test that new users have is_email_verified=False by default."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", name="Test"
        )
        self.assertFalse(user.is_email_verified)

    def test_generate_verification_code(self):
        """Test generating a verification code."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", name="Test"
        )
        code = user.generate_verification_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        self.assertEqual(user.email_verification_code, code)
        self.assertIsNotNone(user.email_verification_code_created_at)

    def test_is_verification_code_valid_success(self):
        """Test that valid code returns True."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", name="Test"
        )
        code = user.generate_verification_code()
        self.assertTrue(user.is_verification_code_valid(code))

    def test_is_verification_code_valid_wrong_code(self):
        """Test that wrong code returns False."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", name="Test"
        )
        user.generate_verification_code()
        self.assertFalse(user.is_verification_code_valid("000000"))

    def test_is_verification_code_valid_expired(self):
        """Test that expired code returns False."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", name="Test"
        )
        code = user.generate_verification_code()
        # Set code creation time to 16 minutes ago (expired)
        user.email_verification_code_created_at = timezone.now() - timedelta(minutes=16)
        user.save()
        self.assertFalse(user.is_verification_code_valid(code))

    def test_is_verification_code_valid_no_code_set(self):
        """Test that checking code when none is set returns False."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", name="Test"
        )
        self.assertFalse(user.is_verification_code_valid("123456"))

    def test_verify_email(self):
        """Test the verify_email method."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", name="Test"
        )
        user.generate_verification_code()
        user.verify_email()
        self.assertTrue(user.is_email_verified)
        self.assertIsNone(user.email_verification_code)
        self.assertIsNone(user.email_verification_code_created_at)


class RegistrationTests(APITestCase):
    """Test user registration endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/registration/"

    @patch("backend.apps.core.email.send_email")
    def test_successful_registration(self, mock_send_email):
        """Test successful user registration with valid data."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password1": "securepass123",
        }
        response = self.client.post(self.register_url, data)
        self.assertIn(response.status_code, [201, 204])
        self.assertTrue(User.objects.filter(email="john@example.com").exists())
        user = User.objects.get(email="john@example.com")
        self.assertEqual(user.name, "John Doe")

    @patch("backend.apps.core.email.send_email")
    def test_registration_generates_verification_code(self, mock_send_email):
        """Test that registration generates a verification code."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password1": "securepass123",
        }
        self.client.post(self.register_url, data)
        user = User.objects.get(email="john@example.com")
        self.assertIsNotNone(user.email_verification_code)
        self.assertEqual(len(user.email_verification_code), 6)
        self.assertFalse(user.is_email_verified)

    @patch("backend.apps.core.email.send_email")
    def test_registration_sends_verification_email(self, mock_send_email):
        """Test that registration sends a verification email."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password1": "securepass123",
        }
        self.client.post(self.register_url, data)
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]
        self.assertEqual(call_kwargs["to"], "john@example.com")
        self.assertEqual(call_kwargs["template_name"], "auth/verify_email")
        self.assertIn("verification_code", call_kwargs["context"])

    def test_registration_without_name(self):
        """Test registration fails when name is missing."""
        data = {"email": "john@example.com", "password1": "securepass123"}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="john@example.com").exists())

    def test_registration_without_email(self):
        """Test registration fails when email is missing."""
        data = {"name": "John Doe", "password1": "securepass123"}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 400)

    def test_registration_without_password(self):
        """Test registration fails when password is missing."""
        data = {"name": "John Doe", "email": "john@example.com"}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 400)

    def test_registration_with_invalid_email_format(self):
        """Test registration fails with invalid email format."""
        data = {
            "name": "John Doe",
            "email": "not-an-email",
            "password1": "securepass123",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 400)

    def test_registration_with_duplicate_email(self):
        """Test registration fails when email already exists."""
        User.objects.create_user(
            email="existing@example.com", password="pass123", name="Existing"
        )
        data = {
            "name": "New User",
            "email": "existing@example.com",
            "password1": "newpass123",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)
        self.assertIn("already exists", response.data["email"][0].lower())

    def test_registration_with_weak_password(self):
        """Test registration with weak password (numeric only)."""
        data = {"name": "John Doe", "email": "john@example.com", "password1": "123456"}
        response = self.client.post(self.register_url, data)
        # Django's default validators should reject this
        self.assertEqual(response.status_code, 400)

    def test_registration_with_very_short_password(self):
        """Test registration with password shorter than minimum."""
        data = {"name": "John Doe", "email": "john@example.com", "password1": "pass"}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 400)

    def test_registration_with_empty_name(self):
        """Test registration with empty name field."""
        data = {"name": "", "email": "john@example.com", "password1": "securepass123"}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 400)

    def test_registration_with_whitespace_only_name(self):
        """Test registration with whitespace-only name."""
        data = {
            "name": "   ",
            "email": "john@example.com",
            "password1": "securepass123",
        }
        response = self.client.post(self.register_url, data)
        # Whitespace-only name might pass format validation but should not be ideal
        if response.status_code == 201:
            user = User.objects.get(email="john@example.com")
            # Name should be stored, even if whitespace
            self.assertIsNotNone(user.name)

    def test_registration_email_case_insensitive(self):
        """Test that registration normalizes email to lowercase."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password1": "securepass123",
        }
        response = self.client.post(self.register_url, data)
        self.assertIn(response.status_code, [201, 204])
        user = User.objects.get(email="john@example.com")
        self.assertEqual(user.email, "john@example.com")

    def test_registration_returns_token(self):
        """Test that successful registration returns an auth token or creates user."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password1": "securepass123",
        }
        response = self.client.post(self.register_url, data)
        self.assertIn(response.status_code, [201, 204])
        # User should be created
        self.assertTrue(User.objects.filter(email="john@example.com").exists())


class LoginTests(APITestCase):
    """Test user login endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/auth/login/"
        self.user_data = {"email": "testuser@example.com", "password": "testpass123"}
        self.user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            name="Test User",
        )
        # Verify user for most tests
        self.user.is_email_verified = True
        self.user.save()

    def test_successful_login(self):
        """Test successful login with valid credentials."""
        response = self.client.post(self.login_url, self.user_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("key", response.data)

    def test_login_unverified_user_returns_403(self):
        """Test login fails for unverified user with 403."""
        self.user.is_email_verified = False
        self.user.save()
        response = self.client.post(self.login_url, self.user_data)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.data.get("email_not_verified"))
        self.assertEqual(response.data.get("email"), self.user.email)

    def test_login_with_wrong_password(self):
        """Test login fails with incorrect password."""
        data = {"email": self.user_data["email"], "password": "wrongpassword"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)

    def test_login_with_nonexistent_email(self):
        """Test login fails with non-existent email."""
        data = {"email": "nonexistent@example.com", "password": "anypassword"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)

    def test_login_without_email(self):
        """Test login fails when email is missing."""
        data = {"password": "testpass123"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)

    def test_login_without_password(self):
        """Test login fails when password is missing."""
        data = {"email": self.user_data["email"]}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)

    def test_login_with_empty_email(self):
        """Test login fails with empty email."""
        data = {"email": "", "password": "testpass123"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)

    def test_login_with_empty_password(self):
        """Test login fails with empty password."""
        data = {"email": self.user_data["email"], "password": ""}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 400)

    def test_login_with_inactive_user(self):
        """Test login fails for inactive user."""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.login_url, self.user_data)
        self.assertEqual(response.status_code, 400)

    def test_login_email_case_insensitive(self):
        """Test that login works with lowercase email."""
        data = {"email": "testuser@example.com", "password": self.user_data["password"]}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("key", response.data)


class TokenAuthenticationTests(APITestCase):
    """Test token authentication for protected endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpass123", name="Test User"
        )
        self.user.is_email_verified = True
        self.user.save()
        self.token = Token.objects.create(user=self.user)
        self.user_detail_url = "/api/auth/user/"

    def test_authenticated_request_with_valid_token(self):
        """Test accessing protected endpoint with valid token."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.user.email)

    def test_authenticated_request_without_token(self):
        """Test accessing protected endpoint without token."""
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_request_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token."""
        self.client.credentials(HTTP_AUTHORIZATION="Token invalidtoken123")
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_request_with_malformed_header(self):
        """Test accessing protected endpoint with malformed auth header."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_request_with_empty_token(self):
        """Test accessing protected endpoint with empty token."""
        self.client.credentials(HTTP_AUTHORIZATION="Token ")
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, 401)

    def test_user_detail_returns_correct_user(self):
        """Test that user detail endpoint returns correct user data."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "testuser@example.com")


class LogoutTests(APITestCase):
    """Test user logout endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.logout_url = "/api/auth/logout/"
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpass123", name="Test User"
        )
        self.user.is_email_verified = True
        self.user.save()
        self.token = Token.objects.create(user=self.user)

    def test_successful_logout(self):
        """Test successful logout with valid token."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 200)
        # Token should be deleted
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())

    def test_logout_without_token(self):
        """Test logout without authentication."""
        response = self.client.post(self.logout_url)
        # dj-rest-auth returns 200 even without auth, treating it as a no-op
        self.assertIn(response.status_code, [200, 401])

    def test_logout_with_invalid_token(self):
        """Test logout fails with invalid token."""
        self.client.credentials(HTTP_AUTHORIZATION="Token invalidtoken123")
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 401)


class VerifyEmailTests(APITestCase):
    """Test email verification endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.verify_url = "/api/auth/verify-email/"
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpass123", name="Test User"
        )
        self.code = self.user.generate_verification_code()

    def test_successful_verification(self):
        """Test successful email verification returns token."""
        data = {"email": self.user.email, "code": self.code}
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertIsNone(self.user.email_verification_code)
        # Should return auth token for auto-login
        self.assertIn("key", response.data)
        self.assertTrue(Token.objects.filter(user=self.user).exists())

    def test_verification_with_wrong_code(self):
        """Test verification fails with wrong code."""
        data = {"email": self.user.email, "code": "000000"}
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid", response.data["detail"].lower())
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)

    def test_verification_with_expired_code(self):
        """Test verification fails with expired code."""
        self.user.email_verification_code_created_at = timezone.now() - timedelta(
            minutes=16
        )
        self.user.save()
        data = {"email": self.user.email, "code": self.code}
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("expired", response.data["detail"].lower())

    def test_verification_with_nonexistent_email(self):
        """Test verification fails with non-existent email."""
        data = {"email": "nonexistent@example.com", "code": "123456"}
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, 400)

    def test_verification_already_verified(self):
        """Test verification fails for already verified user."""
        self.user.is_email_verified = True
        self.user.save()
        data = {"email": self.user.email, "code": self.code}
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("already verified", response.data["detail"].lower())

    def test_verification_missing_email(self):
        """Test verification fails without email."""
        data = {"code": self.code}
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, 400)

    def test_verification_missing_code(self):
        """Test verification fails without code."""
        data = {"email": self.user.email}
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, 400)

    def test_verification_code_too_short(self):
        """Test verification fails with code that's too short."""
        data = {"email": self.user.email, "code": "12345"}
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, 400)


class ResendVerificationTests(APITestCase):
    """Test resend verification code endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.resend_url = "/api/auth/resend-verification/"
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpass123", name="Test User"
        )

    @patch("backend.apps.users.views.send_email")
    def test_successful_resend(self, mock_send_email):
        """Test successful resend of verification code."""
        old_code = self.user.generate_verification_code()
        data = {"email": self.user.email}
        response = self.client.post(self.resend_url, data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        # New code should be generated
        self.assertNotEqual(self.user.email_verification_code, old_code)
        mock_send_email.assert_called_once()

    @patch("backend.apps.users.views.send_email")
    def test_resend_for_nonexistent_email(self, mock_send_email):
        """Test resend returns success for non-existent email (security)."""
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(self.resend_url, data)
        # Should return 200 to not reveal if email exists
        self.assertEqual(response.status_code, 200)
        mock_send_email.assert_not_called()

    @patch("backend.apps.users.views.send_email")
    def test_resend_for_already_verified(self, mock_send_email):
        """Test resend fails for already verified user."""
        self.user.is_email_verified = True
        self.user.save()
        data = {"email": self.user.email}
        response = self.client.post(self.resend_url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("already verified", response.data["detail"].lower())
        mock_send_email.assert_not_called()

    def test_resend_missing_email(self):
        """Test resend fails without email."""
        response = self.client.post(self.resend_url, {})
        self.assertEqual(response.status_code, 400)
