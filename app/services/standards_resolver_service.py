"""L4 — resolve standards from standard_id / standard_ref / catalog metadata."""

from __future__ import annotations

import re
from typing import Any

from app.config.standards_seed import iter_seed_standards
from app.repositories.standards_repository import StandardsRepository
from app.schemas.standards import StandardAndRegulation, StandardResolveResult


def normalize_standard_ref(value: str | None) -> str:
    if not value:
        return ""
    text = str(value).strip().casefold()
    text = text.replace('"', "").replace("״", "").replace("'", "")
    text = re.sub(r"\s+", " ", text)
    return text


def _record_aliases(record: dict[str, Any]) -> list[str]:
    aliases: list[str] = []
    for key in ("standard_code", "title"):
        value = record.get(key)
        if value:
            aliases.append(str(value))
    for alias in record.get("ref_aliases") or []:
        aliases.append(str(alias))
    return aliases


class StandardsResolverService:
    def __init__(
        self,
        *,
        repository: StandardsRepository | None = None,
    ) -> None:
        self.repository = repository or StandardsRepository()

    def resolve_by_id(
        self,
        standard_id: str | None,
    ) -> StandardResolveResult | None:
        normalized = (standard_id or "").strip()
        if not normalized:
            return None

        record = self.repository.get_by_id(normalized)
        if record is None:
            return None

        return self._result_from_record(
            record,
            matched_by="standard_id",
        )

    def resolve_from_ref(
        self,
        standard_ref: str | None,
    ) -> StandardResolveResult | None:
        normalized_ref = normalize_standard_ref(standard_ref)
        if not normalized_ref:
            return None

        for record in self._all_records():
            for alias in _record_aliases(record):
                alias_norm = normalize_standard_ref(alias)
                if not alias_norm:
                    continue
                if (
                    normalized_ref == alias_norm
                    or normalized_ref in alias_norm
                    or alias_norm in normalized_ref
                ):
                    return self._result_from_record(
                        record,
                        matched_by="standard_ref",
                        standard_ref=standard_ref,
                    )

        return None

    def resolve_for_catalog_issue(
        self,
        catalog_issue: dict[str, Any] | None,
    ) -> StandardResolveResult | None:
        if not catalog_issue:
            return None

        explicit_id = catalog_issue.get("standard_id")
        resolved = self.resolve_by_id(
            str(explicit_id) if explicit_id else None
        )
        if resolved is not None:
            return resolved.model_copy(update={"matched_by": "standard_id"})

        for candidate in (
            catalog_issue.get("standard_ref"),
            catalog_issue.get("category_standard_id"),
        ):
            resolved = self.resolve_from_ref(
                str(candidate) if candidate else None
            )
            if resolved is not None:
                return resolved

        return None

    def resolve_for_issue(
        self,
        issue: dict[str, Any],
        *,
        catalog_issue: dict[str, Any] | None = None,
    ) -> StandardResolveResult | None:
        explicit_id = issue.get("standard_id")
        resolved = self.resolve_by_id(
            str(explicit_id) if explicit_id else None
        )
        if resolved is not None:
            return resolved

        if catalog_issue is not None:
            resolved = self.resolve_for_catalog_issue(catalog_issue)
            if resolved is not None:
                return resolved

        for candidate in (
            issue.get("standard_ref"),
            issue.get("category_standard_id"),
        ):
            resolved = self.resolve_from_ref(
                str(candidate) if candidate else None
            )
            if resolved is not None:
                return resolved

        return None

    def _all_records(self) -> list[dict[str, Any]]:
        records = self.repository.list_all()
        if records:
            return records
        return [dict(record) for record in iter_seed_standards()]

    def _result_from_record(
        self,
        record: dict[str, Any],
        *,
        matched_by: str,
        standard_ref: str | None = None,
    ) -> StandardResolveResult:
        standard = StandardAndRegulation.from_record(record)
        return StandardResolveResult(
            standard_id=standard.id,
            standard_code=standard.standard_code,
            title=standard.title,
            category=standard.category,
            recommended_remedy=standard.recommended_remedy,
            matched_by=matched_by,
            standard_ref=standard_ref,
        )
