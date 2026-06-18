"""תוויות עברית לסוגי פרויקט בנייה - mirrors orgflow-ui project-scheme-labels (FR-4.3)."""

from __future__ import annotations

from typing import Literal

ProjectScheme = Literal[
    "TAMA38_STRENGTHENING",
    "TAMA38_DEMOLITION_REBUILD",
    "TAMA38_RELOCATED_BUILD",
    "NEW_CONSTRUCTION",
]

PROJECT_SCHEME_SHORT_LABELS: dict[ProjectScheme, str] = {
    "TAMA38_STRENGTHENING": "חיזוק",
    "TAMA38_DEMOLITION_REBUILD": "הריסה ובניה",
    "TAMA38_RELOCATED_BUILD": "פינוי בינוי",
    "NEW_CONSTRUCTION": "בנייה חדשה",
}

VALID_PROJECT_SCHEMES: frozenset[str] = frozenset(
    PROJECT_SCHEME_SHORT_LABELS.keys()
)


def is_valid_project_scheme(value: str | None) -> bool:
    return value in VALID_PROJECT_SCHEMES


def parse_project_scheme(value: str | None) -> ProjectScheme:
    """Z1 — scheme חובה בהקמת/עדכון פרויקט."""
    if not value or not is_valid_project_scheme(value):
        raise ValueError(
            "project scheme is required and must be one of: "
            + ", ".join(sorted(VALID_PROJECT_SCHEMES))
        )
    return value  # type: ignore[return-value]


def project_scheme_label_he(scheme: str) -> str:
    if scheme == "NEW_CONSTRUCTION":
        return "בנייה חדשה"
    short = PROJECT_SCHEME_SHORT_LABELS.get(scheme)  # type: ignore[arg-type]
    if not short:
        return ""
    return f'התחדשות עירונית - פרויקט {short} תמ"א'
