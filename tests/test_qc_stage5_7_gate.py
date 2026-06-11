"""Gate test - roadmap 5.7 unify AI upload findings → quality_issues."""

from __future__ import annotations

from pathlib import Path

from app.schemas.qc_freeze import get_frozen_surface
from app.schemas.quality_issue import build_upload_finding_materialization_key
from app.services.quality_issue_upload_finding_service import (
    QualityIssueUploadFindingService,
)
from app.services.report_processing_service import ReportProcessingService


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_upload_finding_materialization_key_prefix() -> None:
    assert build_upload_finding_materialization_key("r1", "f1").startswith("upload:")


def test_ai_upload_pipeline_qc_replacement_points_to_registry() -> None:
    surface = get_frozen_surface("ai_upload_pipeline")
    assert surface is not None
    assert "registry" in (surface.qc_replacement or "").lower()


def test_report_processing_wires_upload_finding_materialization() -> None:
    service = ReportProcessingService()
    assert hasattr(service, "upload_finding_materialization")
    assert isinstance(
        service.upload_finding_materialization,
        QualityIssueUploadFindingService,
    )


def test_report_processing_source_links_findings_to_quality_issues() -> None:
    source = (REPO_ROOT / "app/services/report_processing_service.py").read_text(
        encoding="utf-8"
    )
    assert "materialize_from_upload_finding" in source
    assert "_link_finding_to_quality_issue" in source
    assert "quality_issue_id" in source
