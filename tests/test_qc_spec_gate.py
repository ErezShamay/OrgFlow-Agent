from __future__ import annotations

from app.schemas.qc_spec import (
    QC_SPEC_DOCUMENTS,
    QC_SPEC_GATE_CRITERIA,
    QC_SPEC_VERSION,
    is_qc_spec_gate_complete,
    validate_qc_spec_documents,
)


def test_qc_spec_version() -> None:
    assert QC_SPEC_VERSION == "0.6"


def test_all_gate_criteria_documented() -> None:
    assert len(QC_SPEC_GATE_CRITERIA) == 6
    task_ids = {task for _, task in QC_SPEC_GATE_CRITERIA}
    assert task_ids == {"0.1", "0.2", "0.3", "0.4", "0.5", "0.6"}


def test_qc_spec_documents_exist_on_disk() -> None:
    missing = validate_qc_spec_documents()
    assert missing == [], f"Missing spec files: {missing}"
    assert is_qc_spec_gate_complete() is True
    assert "qc-platform-spec.md" in QC_SPEC_DOCUMENTS
    assert "field-supervision-checklist-spec.md" in QC_SPEC_DOCUMENTS
