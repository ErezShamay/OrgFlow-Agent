from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator

from app.lib.email_validation import (
    require_valid_email,
    validate_optional_email,
)

ValidatedEmail = Annotated[str, AfterValidator(require_valid_email)]
OptionalValidatedEmail = Annotated[
    str | None,
    AfterValidator(validate_optional_email),
]
