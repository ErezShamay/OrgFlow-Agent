/**
 * Gate L6 — Competitive Layer v2 end-to-end wiring (COMPETITIVE-LAYER-TASKS.md).
 * Z1–Z4 → V1/V2 → L1–L5 chain must stay connected across backend + UI.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  QUICK_INSPECT_STATUS_MAP,
  defaultInspectModeForDocumentType,
} from "@/lib/field-reports/quick-inspect";

const UI_ROOT = path.resolve(__dirname, "../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

function readBackendSource(relativePath: string): string {
  return readFileSync(path.join(REPO_ROOT, relativePath), "utf8");
}

describe("competitive layer e2e gate L6", () => {
  it("Z1–Z3 — scheme required + spatial bootstrap on project create", () => {
    const projectsPage = readUiSource("app/(dashboard)/projects/page.tsx");
    const projectService = readBackendSource("app/services/project_service.py");
    const bootstrap = readBackendSource(
      "app/services/project_spatial_bootstrap_service.py"
    );

    expect(projectsPage).toContain("scheme");
    expect(projectsPage).toContain("ProjectSchemeSelect");
    expect(existsSync(path.join(UI_ROOT, "components/projects/ProjectSchemeSelect.tsx"))).toBe(
      true
    );
    expect(projectService).toContain("spatial_bootstrap_service");
    expect(bootstrap).toContain("bootstrap");
  });

  it("Z4 — auto offline prep without manual step", () => {
    const hook = readUiSource("hooks/useFieldReportOfflinePrep.ts");
    const runner = readUiSource("lib/field-reports/offline-prep-runner.ts");
    const main = readBackendSource("app/main.py");

    expect(hook).toContain("autoPrepare = true");
    expect(runner).toContain("ensureOfflinePrepForProject");
    expect(main).toContain("/projects/{project_id}/offline-prep");
  });

  it("V1 — quick inspect maps X to DEFECT for supervision", () => {
    const togglePath = path.join(
      UI_ROOT,
      "components/field-reports/supervision/QuickInspectToggle.tsx"
    );
    const editor = readUiSource("components/field-reports/SupervisionChecklistEditor.tsx");

    expect(existsSync(togglePath)).toBe(true);
    expect(editor).toContain("QuickInspectToggle");
    expect(QUICK_INSPECT_STATUS_MAP.defect).toBe("DEFECT");
    expect(defaultInspectModeForDocumentType("weekly_inspection")).toBe("quick");
  });

  it("L1 — defect draft materialization API + client sync hook", () => {
    const draftTs = readUiSource("lib/field-reports/checklist-defect-draft.ts");
    const main = readBackendSource("app/main.py");
    const materialization = readBackendSource(
      "app/services/quality_issue_materialization_service.py"
    );

    expect(main).toContain("/lines/{line_id}/draft-issue");
    expect(materialization).toContain("materialize_draft_from_defect");
    expect(draftTs).toContain("syncSupervisionDefectDraftsForReport");
    expect(draftTs).toContain('visibility: "DRAFT"');
  });

  it("L2 — finalize promotes drafts before materializing duplicates", () => {
    const steps = readBackendSource("app/services/field_report_finalize_steps.py");
    const materialization = readBackendSource(
      "app/services/quality_issue_materialization_service.py"
    );

    expect(steps).toContain("promote_drafts_for_report");
    expect(materialization).toContain("PUBLISHED_FROM_FINALIZE");
    expect(existsSync(path.join(REPO_ROOT, "tests/test_competitive_layer_e2e.py"))).toBe(
      true
    );
  });

  it("L4 — standards KB links catalog standard_id to issues", () => {
    const seed = readBackendSource("app/config/field_report_catalog_supervision_seed.py");
    const resolver = readBackendSource("app/services/standards_resolver_service.py");
    const enrich = readBackendSource("app/services/catalog_standard_ref_resolver.py");

    expect(seed).toContain("standard_id");
    expect(resolver).toContain("resolve_for_catalog_issue");
    expect(enrich).toContain("standard_id");
  });

  it("L5 — resident portal shows tenant_view_status_he", () => {
    const portalView = readUiSource("components/apartments/ResidentPortalView.tsx");
    const portalService = readBackendSource("app/services/resident_portal_service.py");
    const schema = readBackendSource("app/schemas/quality_issue.py");

    expect(schema).toContain("tenant_view_status_he");
    expect(portalService).toContain("tenant_view_status_he");
    expect(portalView).toContain("tenant_view_status_he");
  });
});
