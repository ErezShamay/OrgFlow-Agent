from __future__ import annotations

from pathlib import Path

DEFAULT_ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "csv", "txt", "png", "jpg"}
DEFAULT_MAX_BYTES = 10 * 1024 * 1024
BLOCKED_EXTENSIONS = {"exe", "bat", "cmd", "ps1", "js", "vbs", "sh", "dll"}


class FileUploadValidationService:
    def __init__(
        self,
        *,
        allowed_extensions: set[str] | None = None,
        max_bytes: int | None = None,
    ):
        self.allowed_extensions = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
        self.max_bytes = max_bytes or DEFAULT_MAX_BYTES

    def get_policy(self) -> dict:
        return {
            "allowed_extensions": sorted(self.allowed_extensions),
            "blocked_extensions": sorted(BLOCKED_EXTENSIONS),
            "max_bytes": self.max_bytes,
            "max_megabytes": self.max_bytes / (1024 * 1024),
        }

    def validate_upload(
        self,
        *,
        filename: str,
        file_path: str | None = None,
        size_bytes: int | None = None,
    ) -> dict:
        extension = Path(filename).suffix.lower().lstrip(".")
        issues: list[str] = []

        if extension in BLOCKED_EXTENSIONS:
            issues.append("BLOCKED_EXTENSION")
        elif extension not in self.allowed_extensions:
            issues.append("UNSUPPORTED_EXTENSION")

        if ".." in filename or filename.startswith("/"):
            issues.append("PATH_TRAVERSAL")

        actual_size = size_bytes
        if file_path:
            path = Path(file_path)
            if path.is_file():
                actual_size = path.stat().st_size

        if actual_size is not None and actual_size > self.max_bytes:
            issues.append("FILE_TOO_LARGE")

        return {
            "valid": len(issues) == 0,
            "filename": filename,
            "extension": extension,
            "issues": issues,
            "size_bytes": actual_size,
        }
