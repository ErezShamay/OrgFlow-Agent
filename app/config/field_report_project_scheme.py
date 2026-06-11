"""תוויות עברית לסוג פרויקט תמ״א - mirrors orgflow-ui project-scheme-labels (FR-4.3)."""

from __future__ import annotations

from typing import Literal

ProjectScheme = Literal[
    "TAMA38_STRENGTHENING",
    "TAMA38_DEMOLITION_REBUILD",
    "TAMA38_RELOCATED_BUILD",
]

PROJECT_SCHEME_SHORT_LABELS: dict[ProjectScheme, str] = {
    "TAMA38_STRENGTHENING": "חיזוק",
    "TAMA38_DEMOLITION_REBUILD": "הריסה ובניה",
    "TAMA38_RELOCATED_BUILD": "פינוי בינוי",
}

VALID_PROJECT_SCHEMES: frozenset[str] = frozenset(
    PROJECT_SCHEME_SHORT_LABELS.keys()
)


def is_valid_project_scheme(value: str | None) -> bool:
    return value in VALID_PROJECT_SCHEMES


def project_scheme_label_he(scheme: str) -> str:
    short = PROJECT_SCHEME_SHORT_LABELS.get(scheme)  # type: ignore[arg-type]
    if not short:
        return ""
    return f'התחדשות עירונית - פרויקט {short} תמ"א'
