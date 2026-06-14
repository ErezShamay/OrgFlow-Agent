"""
QC Spec 0.6 - Platform spec gate and document registry.

See docs/qc-spec/qc-platform-spec.md.
"""

from __future__ import annotations

from pathlib import Path

QC_SPEC_VERSION = "0.6"

QC_SPEC_DOCUMENTS: tuple[str, ...] = (
    "qc-platform-spec.md",
    "quality-issue-model.md",
    "quality-issue-events.md",
    "qc-personas-permissions.md",
    "qc-navigation.md",
    "qc-freeze-list.md",
    "field-supervision-checklist-spec.md",
)

QC_SPEC_GATE_CRITERIA: tuple[tuple[str, str], ...] = (
    ("quality_issue_model", "0.1"),
    ("quality_issue_events", "0.2"),
    ("personas_permissions", "0.3"),
    ("navigation", "0.4"),
    ("freeze_list", "0.5"),
    ("consolidated_spec", "0.6"),
)


def qc_spec_root() -> Path:
    return Path(__file__).resolve().parents[2] / "docs" / "qc-spec"


def validate_qc_spec_documents() -> list[str]:
    """Return list of missing spec document filenames."""
    root = qc_spec_root()
    missing: list[str] = []
    for filename in QC_SPEC_DOCUMENTS:
        if not (root / filename).is_file():
            missing.append(filename)
    return missing


def is_qc_spec_gate_complete() -> bool:
    return len(validate_qc_spec_documents()) == 0
