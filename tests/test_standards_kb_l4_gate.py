"""Gate L4 — standards_and_regulations KB (COMPETITIVE-LAYER-TASKS.md)."""

from __future__ import annotations

from pathlib import Path

from app.config.field_report_catalog_supervision_seed import (
    SUPERVISION_CATALOG_ISSUES,
)
from app.config.standards_seed import (
    STANDARD_HLT_VENT_4M3_ID,
    STANDARD_MAMAD_REGS_ID,
    STANDARD_TI_1752_SILL_ID,
    STANDARDS_SEED,
    seed_standard_by_id,
)
from app.db.schema_registry import MIGRATION_SCRIPTS, SCHEMA_VERSION, TABLES
from app.repositories.standards_repository import (
    STANDARDS_MIGRATION,
    StandardsRepository,
)
from app.schemas.standards import StandardAndRegulation
from app.services.catalog_standard_ref_resolver import (
    enrich_issue_standard_ref,
    resolve_catalog_link_for_issue,
)
from app.services.field_report_catalog_service import FieldReportCatalogService
from app.services.standards_resolver_service import StandardsResolverService

REPO_ROOT = Path(__file__).resolve().parents[1]


class InMemoryStandardsRepository:
    def __init__(self, records: list[dict] | None = None) -> None:
        self.records = list(records or [dict(item) for item in STANDARDS_SEED])

    def list_all(self) -> list[dict]:
        return list(self.records)

    def get_by_id(self, standard_id: str) -> dict | None:
        for record in self.records:
            if str(record.get("id")) == standard_id:
                return record
        return None

    def get_by_code(self, standard_code: str) -> dict | None:
        normalized = (standard_code or "").strip().upper()
        for record in self.records:
            if str(record.get("standard_code") or "").upper() == normalized:
                return record
        return None


def test_migration_sql_defines_standards_table() -> None:
    migration_path = REPO_ROOT / STANDARDS_MIGRATION
    sql = migration_path.read_text(encoding="utf-8")

    assert "CREATE TABLE" in sql
    assert "standards_and_regulations" in sql
    assert "standard_code" in sql
    assert "raw_legal_text" in sql
    assert "standards_and_regulations_authenticated_select" in sql


def test_migration_registered_in_schema_registry() -> None:
    assert SCHEMA_VERSION == "2026061803"

    entry = next(
        script
        for script in MIGRATION_SCRIPTS
        if script["version"] == "2026061802"
    )
    assert entry["name"] == "standards_and_regulations"
    assert entry["tables"] == ["standards_and_regulations"]

    schema = TABLES["standards_and_regulations"]
    assert schema.tenant_column is None
    assert schema.rls_policies[0].using_expression == "true"


def test_seed_contains_three_minimum_standards() -> None:
    assert len(STANDARDS_SEED) == 3

    ti_1752 = seed_standard_by_id(STANDARD_TI_1752_SILL_ID)
    mamad = seed_standard_by_id(STANDARD_MAMAD_REGS_ID)
    vent = seed_standard_by_id(STANDARD_HLT_VENT_4M3_ID)

    assert ti_1752 is not None
    assert "1752" in ti_1752["title"]
    assert "מפתנים" in ti_1752["title"]

    assert mamad is not None
    assert "ממ" in mamad["title"]

    assert vent is not None
    assert "וונטה" in vent["title"]
    assert "4" in vent["title"]


def test_standard_schema_validates_seed() -> None:
    for record in STANDARDS_SEED:
        standard = StandardAndRegulation.from_record(record)
        assert standard.standard_code
        assert standard.raw_legal_text


def test_resolver_maps_standard_ref_to_uuid() -> None:
    resolver = StandardsResolverService(
        repository=InMemoryStandardsRepository(),
    )

    by_ref = resolver.resolve_from_ref('ת"י 1752')
    assert by_ref is not None
    assert by_ref.standard_id == STANDARD_TI_1752_SILL_ID
    assert by_ref.matched_by == "standard_ref"

    by_id = resolver.resolve_by_id(STANDARD_MAMAD_REGS_ID)
    assert by_id is not None
    assert by_id.standard_code == "MAMAD-REGS"


def test_catalog_issue_with_standard_id_resolves() -> None:
    catalog = FieldReportCatalogService()
    issue = catalog.find_issue("SUP-SAFE-001")
    assert issue is not None
    assert issue.get("standard_id") == STANDARD_MAMAD_REGS_ID

    resolver = StandardsResolverService(
        repository=InMemoryStandardsRepository(),
    )
    resolved = resolver.resolve_for_catalog_issue(issue)
    assert resolved is not None
    assert resolved.standard_id == STANDARD_MAMAD_REGS_ID


def test_enrich_issue_standard_ref_adds_standard_id() -> None:
    resolver = StandardsResolverService(
        repository=InMemoryStandardsRepository(),
    )
    enriched = enrich_issue_standard_ref(
        {
            "catalog_issue_id": "SUP-INS-007",
            "standard_ref": None,
        },
        catalog_service=FieldReportCatalogService(),
        standards_resolver=resolver,
    )

    assert enriched["standard_id"] == STANDARD_TI_1752_SILL_ID
    assert '1752' in (enriched.get("standard_ref") or "")


def test_resolve_catalog_link_includes_standard_id() -> None:
    resolver = StandardsResolverService(
        repository=InMemoryStandardsRepository(),
    )
    link = resolve_catalog_link_for_issue(
        catalog_issue_id="SUP-MEP-VENT-001",
        catalog_service=FieldReportCatalogService(),
        standards_resolver=resolver,
    )

    assert link is not None
    assert link.standard_id == STANDARD_HLT_VENT_4M3_ID


def test_supervision_seed_links_known_standards() -> None:
    by_id = {
        str(item.get("standard_id")): item
        for item in SUPERVISION_CATALOG_ISSUES
        if item.get("standard_id")
    }
    assert STANDARD_TI_1752_SILL_ID in by_id
    assert STANDARD_MAMAD_REGS_ID in by_id
    assert STANDARD_HLT_VENT_4M3_ID in by_id


def test_l4_files_wired() -> None:
    assert (REPO_ROOT / "app/schemas/standards.py").is_file()
    assert (REPO_ROOT / "app/repositories/standards_repository.py").is_file()
    assert (REPO_ROOT / "app/services/standards_resolver_service.py").is_file()
    assert StandardsRepository is not None
