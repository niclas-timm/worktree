from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EmailPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class EmailMessage:
    """Data class representing an email to be sent."""

    to: list[str]
    subject: str
    template_name: str
    context: dict[str, Any] = field(default_factory=dict)
    from_email: str | None = None
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    reply_to: list[str] = field(default_factory=list)
    attachments: list[tuple[str, bytes, str]] = field(default_factory=list)
    priority: EmailPriority = EmailPriority.NORMAL
