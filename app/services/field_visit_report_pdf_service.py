from __future__ import annotations

import re
from pathlib import Path

from app.exceptions.exceptions import ValidationError

MAX_PDF_BYTES = 15 * 1024 * 1024
PDFS_ROOT = Path("field_report_pdfs")


class FieldVisitReportPdfService:
    def __init__(self, *, pdfs_root: Path | None = None) -> None:
        self.pdfs_root = pdfs_root or PDFS_ROOT

    def build_storage_path(
        self,
        *,
        organization_id: str,
        project_id: str,
        report_id: str,
        filename: str,
    ) -> str:
        safe_filename = self.sanitize_filename(filename)
        return (
            f"{organization_id}/{project_id}/{report_id}/{safe_filename}"
        )

    def resolve_absolute_path(self, storage_path: str) -> Path:
        return self.pdfs_root / storage_path

    def save_pdf(
        self,
        *,
        organization_id: str,
        project_id: str,
        report_id: str,
        content: bytes,
        filename: str,
    ) -> tuple[str, str]:
        self._validate_pdf(content=content, filename=filename)
        safe_filename = self.sanitize_filename(filename)
        storage_path = self.build_storage_path(
            organization_id=organization_id,
            project_id=project_id,
            report_id=report_id,
            filename=safe_filename,
        )
        target = self.resolve_absolute_path(storage_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return storage_path, safe_filename

    def read_pdf(self, storage_path: str) -> tuple[bytes, str]:
        target = self.resolve_absolute_path(storage_path)
        if not target.is_file():
            raise FileNotFoundError(storage_path)

        return target.read_bytes(), "application/pdf"

    def delete_pdf(self, storage_path: str | None) -> None:
        if not storage_path:
            return

        target = self.resolve_absolute_path(storage_path)
        if target.is_file():
            target.unlink()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        trimmed = (filename or "visit-report.pdf").strip()
        safe = re.sub(r"[^\w.\-א-ת\s]", "_", trimmed)
        safe = re.sub(r"\s+", "_", safe).strip("._")
        if not safe:
            safe = "visit-report.pdf"
        if not safe.lower().endswith(".pdf"):
            safe = f"{safe}.pdf"
        return safe

    @staticmethod
    def _validate_pdf(*, content: bytes, filename: str) -> None:
        if not content:
            raise ValidationError(message="קובץ ה-PDF ריק")

        if len(content) > MAX_PDF_BYTES:
            raise ValidationError(
                message="גודל ה-PDF חורג מהמותר (15MB)",
            )

        if not content.startswith(b"%PDF"):
            raise ValidationError(
                message="קובץ ה-PDF אינו תקין",
            )

        if b"%%EOF" not in content[-2048:]:
            raise ValidationError(
                message="קובץ ה-PDF נראה פגום או לא שלם",
            )

        extension = Path(filename or "").suffix.lower()
        if extension and extension != ".pdf":
            raise ValidationError(
                message="יש להעלות קובץ PDF בלבד",
            )
