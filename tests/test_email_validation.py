from __future__ import annotations

import pytest

from app.lib.email_validation import (
    is_valid_email,
    require_valid_email,
    validate_optional_email,
)
from app.schemas.email_fields import ValidatedEmail
from pydantic import BaseModel, ValidationError


class EmailPayload(BaseModel):
    email: ValidatedEmail


@pytest.mark.parametrize(
    "email",
    [
        "erez@erez.com",
        "user.name+tag@example.co.il",
        "noa@company.org.il",
        "A@B.CO.IL",
    ],
)
def test_is_valid_email_accepts_well_formed_addresses(email: str) -> None:
    assert is_valid_email(email)


@pytest.mark.parametrize(
    "email",
    [
        "",
        "not-an-email",
        "missing-at-sign.com",
        "@example.com",
        "user@",
        "user@domain",
        "user@@example.com",
        "user@.com",
        "user@domain.",
    ],
)
def test_is_valid_email_rejects_invalid_addresses(email: str) -> None:
    assert not is_valid_email(email)


def test_require_valid_email_normalizes_case() -> None:
    assert require_valid_email("  User@Example.COM ") == "user@example.com"


def test_validate_optional_email_allows_empty_values() -> None:
    assert validate_optional_email(None) is None
    assert validate_optional_email("") is None
    assert validate_optional_email("   ") is None


def test_validate_optional_email_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="invalid email address"):
        validate_optional_email("bad-email")


def test_pydantic_validated_email_field() -> None:
    payload = EmailPayload(email="owner@example.co.il")
    assert payload.email == "owner@example.co.il"

    with pytest.raises(ValidationError):
        EmailPayload(email="owner@invalid")
