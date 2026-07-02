"""
Field report checklist scopes and document types (F8 — §20).

Content lives in docs/FIELD-REPORT-CHECKLISTS.md.
Catalog seed: app/config/field_report_catalog_supervision_seed.py
"""

from __future__ import annotations

from typing import Literal

FieldReportDocumentType = Literal[
    "weekly_inspection",
    "handover_protocol",
]

VisitScopeWeekly = Literal[
    "APARTMENT",
    "PUBLIC_AREA",
    "WHOLE_BUILDING",
    "MULTI_APARTMENT",
]
VisitScopeHandover = Literal["HANDOVER"]

FIELD_REPORT_DOCUMENT_TYPES: tuple[FieldReportDocumentType, ...] = (
    "weekly_inspection",
    "handover_protocol",
)

VISIT_SCOPES_WEEKLY: tuple[VisitScopeWeekly, ...] = (
    "APARTMENT",
    "PUBLIC_AREA",
    "WHOLE_BUILDING",
    "MULTI_APARTMENT",
)
VISIT_SCOPE_HANDOVER: VisitScopeHandover = "HANDOVER"

# Wizard placeholder — enable when handover checklist content is approved (§20).
HANDOVER_PROTOCOL_WIZARD_ENABLED: bool = False
