import datetime
import logging
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from .exceptions import EmailSendError, EmailTemplateNotFoundError
from .types import EmailMessage, EmailPriority

logger = logging.getLogger(__name__)


class EmailService:
    """
    Reusable email service for sending templated emails.

    Usage:
        # Simple usage
        service = EmailService()
        service.send(
            to=["user@example.com"],
            subject="Welcome!",
            template_name="users/welcome",
            context={"user_name": "John"}
        )

        # Using EmailMessage dataclass
        msg = EmailMessage(
            to=["user@example.com"],
            subject="Welcome!",
            template_name="users/welcome",
            context={"user_name": "John"}
        )
        service.send_message(msg)
    """

    def __init__(
        self,
        from_email: str | None = None,
        fail_silently: bool = False,
    ):
        self.from_email = from_email or getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"
        )
        self.fail_silently = fail_silently

    def send(
        self,
        to: str | list[str],
        subject: str,
        template_name: str,
        context: dict[str, Any] | None = None,
        from_email: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: list[str] | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
        priority: EmailPriority = EmailPriority.NORMAL,
    ) -> bool:
        """
        Send a templated email.

        Args:
            to: Recipient email address(es)
            subject: Email subject line
            template_name: Template path without extension (e.g., "users/welcome")
            context: Template context variables
            from_email: Override default sender
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to addresses
            attachments: List of (filename, content, mimetype) tuples
            priority: Email priority level

        Returns:
            True if email was sent successfully

        Raises:
            EmailTemplateNotFoundError: If template doesn't exist
            EmailSendError: If sending fails and fail_silently is False
        """
        if isinstance(to, str):
            to = [to]

        full_context = self._build_context(context or {})

        html_content = self._render_template(template_name, "html", full_context)
        text_content = self._render_template(template_name, "txt", full_context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email or self.from_email,
            to=to,
            cc=cc or [],
            bcc=bcc or [],
            reply_to=reply_to or [],
        )

        if html_content:
            email.attach_alternative(html_content, "text/html")

        for filename, content, mimetype in attachments or []:
            email.attach(filename, content, mimetype)

        self._set_priority_headers(email, priority)

        try:
            email.send(fail_silently=self.fail_silently)
            logger.info(f"Email sent successfully to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            if not self.fail_silently:
                raise EmailSendError(f"Failed to send email: {e}") from e
            return False

    def send_message(self, message: EmailMessage) -> bool:
        """Send an email using an EmailMessage dataclass."""
        return self.send(
            to=message.to,
            subject=message.subject,
            template_name=message.template_name,
            context=message.context,
            from_email=message.from_email,
            cc=message.cc,
            bcc=message.bcc,
            reply_to=message.reply_to,
            attachments=message.attachments,
            priority=message.priority,
        )

    def _build_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build template context with default variables."""
        defaults = {
            "site_name": getattr(settings, "SITE_NAME", "Ticketing"),
            "site_url": getattr(settings, "SITE_URL", "http://localhost:3000"),
            "support_email": getattr(settings, "SUPPORT_EMAIL", self.from_email),
            "current_year": datetime.datetime.now().year,
        }
        return {**defaults, **context}

    def _render_template(
        self,
        template_name: str,
        extension: str,
        context: dict[str, Any],
    ) -> str | None:
        """
        Render a template with the given context.

        Args:
            template_name: Base template name without extension
            extension: File extension (html or txt)
            context: Template context

        Returns:
            Rendered template string or None if template doesn't exist
        """
        template_path = f"email/{template_name}.{extension}"
        try:
            return render_to_string(template_path, context)
        except TemplateDoesNotExist:
            if extension == "html":
                logger.warning(f"HTML template not found: {template_path}")
                return None
            raise EmailTemplateNotFoundError(
                f"Email template not found: {template_path}"
            )

    def _set_priority_headers(
        self,
        email: EmailMultiAlternatives,
        priority: EmailPriority,
    ) -> None:
        """Set email priority headers."""
        priority_map = {
            EmailPriority.HIGH: ("1", "high"),
            EmailPriority.NORMAL: ("3", "normal"),
            EmailPriority.LOW: ("5", "low"),
        }
        x_priority, importance = priority_map[priority]
        email.extra_headers["X-Priority"] = x_priority
        email.extra_headers["Importance"] = importance


_default_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get or create the default email service instance."""
    global _default_service
    if _default_service is None:
        _default_service = EmailService()
    return _default_service


def send_email(
    to: str | list[str],
    subject: str,
    template_name: str,
    context: dict[str, Any] | None = None,
    **kwargs,
) -> bool:
    """
    Convenience function to send an email using the default service.

    Example:
        from backend.apps.core.email import send_email

        send_email(
            to="user@example.com",
            subject="Welcome!",
            template_name="users/welcome",
            context={"user_name": "John"}
        )
    """
    return get_email_service().send(
        to=to,
        subject=subject,
        template_name=template_name,
        context=context,
        **kwargs,
    )
