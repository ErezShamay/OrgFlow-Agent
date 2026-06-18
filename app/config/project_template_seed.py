"""Z2 — global project template seed (spatial layout, not checklist content)."""

from __future__ import annotations

from typing import Any

from app.config.field_report_project_scheme import ProjectScheme

# Mirrors orgflow-ui PUBLIC_AREA_DEFINITIONS (field-supervision-checklist).
DEFAULT_PUBLIC_AREA_IDS: tuple[str, ...] = (
    "LOBBY",
    "WET_ROOMS",
    "BALCONY_ROOF",
    "PARKING",
    "ELEVATOR_STAIRS",
    "OUTDOOR",
)

TAMA38_STRENGTHENING_TEMPLATE_ID = (
    "00000000-0000-4000-8000-000000000001"
)

PROJECT_TEMPLATE_SEED: tuple[dict[str, Any], ...] = (
    {
        "id": TAMA38_STRENGTHENING_TEMPLATE_ID,
        "organization_id": None,
        "scheme": "TAMA38_STRENGTHENING",
        "template_name_he": 'תמ"א 38/1 — חיזוק (ברירת מחדל)',
        "default_floors": 7,
        "default_units_per_floor": 4,
        "public_area_ids": list(DEFAULT_PUBLIC_AREA_IDS),
        "catalog_filter": None,
        "is_active": True,
    },
)


def iter_seed_templates() -> tuple[dict[str, Any], ...]:
    return PROJECT_TEMPLATE_SEED


def seed_template_for_scheme(scheme: str) -> dict[str, Any] | None:
    for template in PROJECT_TEMPLATE_SEED:
        if template["scheme"] == scheme and template.get("is_active", True):
            return dict(template)
    return None


def is_known_public_area_id(value: str) -> bool:
    return value in DEFAULT_PUBLIC_AREA_IDS
