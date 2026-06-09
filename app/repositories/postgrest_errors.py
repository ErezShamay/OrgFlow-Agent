from postgrest.exceptions import APIError

from app.exceptions.exceptions import ValidationError


def is_missing_column_error(
    error: APIError,
    column: str,
) -> bool:
    message = str(error).lower()
    code = getattr(error, "code", None)
    column_lower = column.lower()

    if column_lower not in message:
        return False

    return (
        code in ("PGRST204", "42703")
        or "could not find" in message
        or "does not exist" in message
    )


def raise_if_missing_column_migration(
    error: APIError,
    *,
    column: str,
    migration_file: str,
) -> None:
    """Map PostgREST missing-column errors to a Hebrew migration hint."""
    if is_missing_column_error(error, column):
        raise ValidationError(
            message=(
                f"עמודת {column} חסרה במסד הנתונים. "
                f"יש להריץ את המיגרציה {migration_file}"
            ),
            details={
                "column": column,
                "migration_file": migration_file,
            },
        ) from error

    raise error


def is_invalid_uuid_error(error: APIError) -> bool:
    code = getattr(error, "code", None)
    if code == "22P02":
        return True

    return "invalid input syntax for type uuid" in str(error).lower()


def is_missing_table_error(error: APIError, table: str) -> bool:
    message = str(error).lower()
    code = getattr(error, "code", None)
    table_lower = table.lower()

    if table_lower not in message:
        return False

    return (
        code in ("PGRST205", "42P01")
        or "could not find" in message
        or "does not exist" in message
        or "schema cache" in message
    )
