"""Prefill דוח שטח מישות פרויקט - metadata + stakeholders (FR-4.3)."""

from __future__ import annotations

from app.config.field_report_project_scheme import (
    is_valid_project_scheme,
    project_scheme_label_he,
)

STAKEHOLDER_ROLE_LABELS_HE: dict[str, str] = {
    "developer": "יזם",
    "project_manager": "מנהל פרויקט מטעם יזם",
    "site_manager": "מנהל עבודה",
    "contractor": "קבלן מבצע",
    "lawyer_tenants": "עו״ד ב״כ דיירים",
    "lawyer_accompanying": "עו״ד מלווה",
    "architect": "אדריכל הפרויקט",
}

_PROJECT_FIELD_BY_ROLE: tuple[tuple[str, str], ...] = (
    ("developer", "developer_name"),
    ("project_manager", "developer_pm_name"),
    ("site_manager", "site_manager_name"),
    ("contractor", "contractor_name"),
    ("lawyer_tenants", "lawyer_name"),
    ("lawyer_accompanying", "accompanying_lawyer"),
    ("architect", "architect_name"),
)


def _pick_name(project: dict, *keys: str) -> str | None:
    for key in keys:
        value = project.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def project_metadata_from_project(project: dict) -> dict:
    """בונה project_metadata לכותרת דוח - רק שדות זמינים בפרויקט."""
    metadata: dict = {}

    scheme = project.get("scheme")
    if is_valid_project_scheme(scheme):
        metadata["scheme"] = scheme
        metadata["scheme_label_he"] = project_scheme_label_he(scheme)

    site_address = _pick_name(project, "city", "site_address")
    if site_address:
        metadata["site_address"] = site_address

    architect_name = _pick_name(project, "architect_name")
    if architect_name:
        metadata["architect_name"] = architect_name

    for key in (
        "housing_units_count",
        "project_start_date",
        "project_end_date",
        "project_grace_end_date",
        "structure_documentation_date",
        "illustration_url",
        "illustration_source_he",
    ):
        value = project.get(key)
        if value is None or value == "":
            continue
        metadata[key] = value

    return metadata


def stakeholders_from_project(project: dict) -> list[dict]:
    """בונה stakeholders משדות פרויקט (מקביל ל-UI project-stakeholder-prefill)."""
    stakeholders: list[dict] = []

    for role, field in _PROJECT_FIELD_BY_ROLE:
        if role == "project_manager":
            name = _pick_name(
                project,
                "developer_pm_name",
                "contractor_name",
            )
        else:
            name = _pick_name(project, field)

        if not name:
            continue

        stakeholders.append(
            {
                "id": f"prefill-{role}",
                "role": role,
                "name": name,
                "label_he": STAKEHOLDER_ROLE_LABELS_HE[role],
            }
        )

    return stakeholders


def merge_project_prefill_into_header_fields(
    project: dict,
    header_fields: dict,
) -> dict:
    """
    ממזג prefill מפרויקט ל-header_fields קיימים.
    ערכים שכבר נשלחו בבקשה (header_fields) גוברים על prefill.
    """
    merged = dict(header_fields)

    prefill_metadata = project_metadata_from_project(project)
    existing_metadata = merged.get("project_metadata")
    if isinstance(existing_metadata, dict):
        merged["project_metadata"] = {
            **prefill_metadata,
            **existing_metadata,
        }
    elif prefill_metadata:
        merged["project_metadata"] = prefill_metadata

    metadata = merged.get("project_metadata")
    if isinstance(metadata, dict):
        if metadata.get("scheme") and not merged.get("scheme"):
            merged["scheme"] = metadata["scheme"]
        if metadata.get("scheme_label_he") and not merged.get(
            "scheme_label_he"
        ):
            merged["scheme_label_he"] = metadata["scheme_label_he"]

    stakeholders = merged.get("stakeholders")
    if not isinstance(stakeholders, list) or not stakeholders:
        prefill_stakeholders = stakeholders_from_project(project)
        if prefill_stakeholders:
            merged["stakeholders"] = prefill_stakeholders

    return merged
