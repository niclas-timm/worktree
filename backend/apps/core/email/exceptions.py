class EmailError(Exception):
    """Base exception for email-related errors."""

    pass


class EmailTemplateNotFoundError(EmailError):
    """Raised when email template cannot be found."""

    pass


class EmailSendError(EmailError):
    """Raised when email fails to send."""

    pass


class EmailConfigurationError(EmailError):
    """Raised when email is misconfigured."""

    pass
