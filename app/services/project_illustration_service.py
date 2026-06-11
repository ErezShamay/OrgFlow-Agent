from __future__ import annotations

import mimetypes
from pathlib import Path

from app.exceptions.exceptions import ValidationError

ALLOWED_ILLUSTRATION_CONTENT_TYPES = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
})
MAX_ILLUSTRATION_BYTES = 8 * 1024 * 1024
ILLUSTRATIONS_ROOT = Path("project_illustrations")


class ProjectIllustrationService:
    def __init__(self, *, illustrations_root: Path | None = None) -> None:
        self.illustrations_root = illustrations_root or ILLUSTRATIONS_ROOT

    def build_storage_path(
        self,
        *,
        organization_id: str,
        project_id: str,
        extension: str,
    ) -> str:
        safe_ext = extension.lower().lstrip(".")
        if safe_ext == "jpg":
            safe_ext = "jpeg"
        return f"{organization_id}/{project_id}.{safe_ext}"

    def resolve_absolute_path(self, storage_path: str) -> Path:
        return self.illustrations_root / storage_path

    def save_illustration(
        self,
        *,
        organization_id: str,
        project_id: str,
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
            project_id=project_id,
            extension=extension,
        )
        target = self.resolve_absolute_path(storage_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return storage_path

    def read_illustration(self, storage_path: str) -> tuple[bytes, str]:
        target = self.resolve_absolute_path(storage_path)
        if not target.is_file():
            raise FileNotFoundError(storage_path)

        content = target.read_bytes()
        guessed, _ = mimetypes.guess_type(str(target))
        return content, guessed or "image/jpeg"

    def _validate_upload(
        self,
        *,
        content: bytes,
        content_type: str | None,
        filename: str | None,
    ) -> None:
        if not content:
            raise ValidationError(message="קובץ התמונה ריק")

        if len(content) > MAX_ILLUSTRATION_BYTES:
            raise ValidationError(
                message="גודל תמונת ההדמיה חורג מ-8MB"
            )

        normalized_type = (content_type or "").split(";", 1)[0].strip().lower()
        if normalized_type and normalized_type not in ALLOWED_ILLUSTRATION_CONTENT_TYPES:
            raise ValidationError(
                message="סוג קובץ לא נתמך - יש להעלות JPG, PNG או WebP"
            )

        if filename:
            extension = Path(filename).suffix.lower()
            if extension and extension not in {".jpg", ".jpeg", ".png", ".webp"}:
                raise ValidationError(
                    message="סוג קובץ לא נתמך - יש להעלות JPG, PNG או WebP"
                )

    def _extension_for(
        self,
        *,
        content_type: str | None,
        filename: str | None,
    ) -> str:
        normalized_type = (content_type or "").split(";", 1)[0].strip().lower()
        if normalized_type == "image/png":
            return "png"
        if normalized_type == "image/webp":
            return "webp"
        if normalized_type == "image/jpeg":
            return "jpeg"

        if filename:
            extension = Path(filename).suffix.lower().lstrip(".")
            if extension in {"jpg", "jpeg", "png", "webp"}:
                return "jpeg" if extension == "jpg" else extension

        return "jpeg"
