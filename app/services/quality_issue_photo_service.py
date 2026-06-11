from __future__ import annotations

import mimetypes
from pathlib import Path

from app.exceptions.exceptions import ValidationError

ALLOWED_IMAGE_CONTENT_TYPES = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
})
MAX_PHOTO_BYTES = 5 * 1024 * 1024
PHOTOS_ROOT = Path("quality_issue_photos")


class QualityIssuePhotoService:
    def __init__(self, *, photos_root: Path | None = None) -> None:
        self.photos_root = photos_root or PHOTOS_ROOT

    def build_storage_path(
        self,
        *,
        organization_id: str,
        issue_id: str,
        extension: str,
        photo_id: str,
    ) -> str:
        safe_ext = extension.lower().lstrip(".")
        if safe_ext == "jpg":
            safe_ext = "jpeg"
        return f"{organization_id}/{issue_id}/{photo_id}.{safe_ext}"

    def resolve_absolute_path(self, storage_path: str) -> Path:
        return self.photos_root / storage_path

    def save_photo(
        self,
        *,
        organization_id: str,
        issue_id: str,
        photo_id: str,
        content: bytes,
        content_type: str | None,
        filename: str | None = None,
    ) -> str:
        self._validate_upload(
            content=content,
            content_type=content_type,
            filename=filename,
        )

        extension = self._extension_for(
            content_type=content_type,
            filename=filename,
        )
        storage_path = self.build_storage_path(
            organization_id=organization_id,
            issue_id=issue_id,
            extension=extension,
            photo_id=photo_id,
        )
        target = self.resolve_absolute_path(storage_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return storage_path

    def read_photo(self, storage_path: str) -> tuple[bytes, str]:
        target = self.resolve_absolute_path(storage_path)
        if not target.is_file():
            raise FileNotFoundError(storage_path)

        content = target.read_bytes()
        content_type = (
            mimetypes.guess_type(target.name)[0]
            or "application/octet-stream"
        )
        return content, content_type

    @staticmethod
    def _validate_upload(
        *,
        content: bytes,
        content_type: str | None,
        filename: str | None,
    ) -> None:
        if not content:
            raise ValidationError(message="קובץ התמונה ריק")

        if len(content) > MAX_PHOTO_BYTES:
            raise ValidationError(
                message="גודל התמונה חורג מהמותר (5MB)",
            )

        normalized_type = (content_type or "").split(";")[0].strip().lower()
        if normalized_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            guessed, _ = mimetypes.guess_type(filename or "")
            normalized_type = (guessed or "").lower()

        if normalized_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise ValidationError(
                message="סוג קובץ לא נתמך. השתמש ב-JPEG, PNG או WebP",
            )

    @staticmethod
    def _extension_for(
        *,
        content_type: str | None,
        filename: str | None,
    ) -> str:
        normalized_type = (content_type or "").split(";")[0].strip().lower()
        if normalized_type == "image/jpeg":
            return "jpeg"
        if normalized_type == "image/png":
            return "png"
        if normalized_type == "image/webp":
            return "webp"

        guessed, _ = mimetypes.guess_type(filename or "")
        if guessed == "image/jpeg":
            return "jpeg"
        if guessed == "image/png":
            return "png"
        if guessed == "image/webp":
            return "webp"

        return "jpeg"
