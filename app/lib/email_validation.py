from __future__ import annotations

import re

INVALID_EMAIL_MESSAGE = "invalid email address"

# local@domain.tld — supports multi-part TLDs such as .co.il
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$"
)

MAX_EMAIL_LENGTH = 320


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    candidate = email.strip()
    if not candidate or len(candidate) > MAX_EMAIL_LENGTH:
        return False
    return EMAIL_PATTERN.fullmatch(candidate) is not None


def require_valid_email(email: str) -> str:
    normalized = normalize_email(email)
    if not is_valid_email(normalized):
        raise ValueError(INVALID_EMAIL_MESSAGE)
    return normalized


def validate_optional_email(email: str | None) -> str | None:
    if email is None:
        return None

    trimmed = email.strip()
    if not trimmed:
        return None

    return require_valid_email(trimmed)
