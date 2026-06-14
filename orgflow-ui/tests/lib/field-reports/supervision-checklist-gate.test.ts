/**
 * Gate — שלב H (field-supervision-checklist-spec §16.H).
 * סגירת מימוש v1: כל שלבי A–G + קריטריוני קבלה §17.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");
const QC_SPEC_ROOT = path.join(REPO_ROOT, "docs", "qc-spec");

const STAGE_GATE_TESTS = [
  "tests/lib/field-reports/supervision-checklist-a-gate.test.ts",
  "tests/lib/field-reports/supervision-checklist-b-gate.test.ts",
  "tests/lib/field-reports/supervision-checklist-c-gate.test.ts",
  "tests/lib/field-reports/supervision-checklist-d-gate.test.ts",
  "tests/lib/field-reports/supervision-checklist-e-gate.test.ts",
  "tests/lib/field-reports/supervision-checklist-f-gate.test.ts",
  "tests/lib/field-reports/supervision-checklist-pdf-gate.test.ts",
] as const;

const UNIT_TESTS = [
  "tests/lib/field-reports/supervision-checklist-builder.test.ts",
  "tests/lib/field-reports/checklist-close-validation.test.ts",
  "tests/lib/field-reports/checklist-defect-to-line.test.ts",
  "tests/lib/field-reports/checklist-photo-store.test.ts",
] as const;

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

function readRepoSource(relativePath: string): string {
  return readFileSync(path.join(REPO_ROOT, relativePath), "utf8");
}

describe("supervision checklist final gate (§16.H + §17)", () => {
  it("spec document exists and is registered in qc_spec.py", () => {
    const specPath = path.join(
      QC_SPEC_ROOT,
      "field-supervision-checklist-spec.md"
    );
    const qcSpec = readRepoSource("app/schemas/qc_spec.py");
    const readme = readUiSource("README.md");

    expect(existsSync(specPath)).toBe(true);
    expect(qcSpec).toContain("field-supervision-checklist-spec.md");
    expect(readme).toContain("field-supervision-checklist-spec.md");
    expect(readme).toContain("supervision-checklist-gate.test.ts");
  });

  it("includes all stage gate tests A–G", () => {
    for (const gatePath of STAGE_GATE_TESTS) {
      expect(existsSync(path.join(UI_ROOT, gatePath))).toBe(true);
    }
  });

  it("includes unit tests from §18.1", () => {
    for (const testPath of UNIT_TESTS) {
      expect(existsSync(path.join(UI_ROOT, testPath))).toBe(true);
    }
  });

  it("§18.3 includes pytest E2E loop for sync → close → publish", () => {
    const e2e = readRepoSource("tests/test_supervision_checklist_e2e.py");

    expect(existsSync(path.join(REPO_ROOT, "tests/test_supervision_checklist_e2e.py"))).toBe(
      true
    );
    expect(e2e).toContain("supervision_checklist");
    expect(e2e).toContain("/field-reports/offline-prep");
    expect(e2e).toContain("/field-reports/visits/sync");
    expect(e2e).toContain("/close");
    expect(e2e).toContain("/publish");
  });

  it("§17.1 flow — project entry only, no list CTA, one unit per report", () => {
    const link = readUiSource("components/field-reports/ProjectFieldReportLink.tsx");
    const listPage = readUiSource("app/(dashboard)/field-reports/page.tsx");
    const newReport = readUiSource("lib/field-reports/supervision-new-report.ts");
    const builder = readUiSource("lib/field-reports/supervision-checklist-builder.ts");

    expect(link).toContain("projectFieldReportNewPath");
    expect(link).toContain("הפקת דוח");
    expect(listPage).not.toContain('href="/field-reports/new"');
    expect(listPage).not.toContain("דוח ביקור חדש");
    expect(newReport).toContain("createSupervisionLocalReport");
    expect(builder).toContain("isSupervisionChecklistReport");
  });

  it("§17.2 checklist — grouping, standard_ref, four statuses", () => {
    const editor = readUiSource("components/field-reports/SupervisionChecklistEditor.tsx");
    const labels = readUiSource("lib/field-reports/supervision-labels.ts");
    const pdfSection = readUiSource(
      "lib/field-reports/pdf/supervision-checklist-pdf-section.ts"
    );

    expect(editor).toContain("groupSupervisionChecklistItems");
    expect(editor).toContain("standard_ref");
    expect(labels).toContain("CHECKLIST_ITEM_STATUS_LABELS");
    expect(labels).toContain("UNCHECKED");
    expect(labels).toContain("OK");
    expect(labels).toContain("DEFECT");
    expect(labels).toContain("NOT_APPLICABLE");
    expect(pdfSection).toContain("groupSupervisionChecklistItems");
  });

  it("§17.3 photos — max 3, DEFECT requires photo before close", () => {
    const validation = readUiSource("lib/field-reports/checklist-close-validation.ts");
    const constants = readUiSource("lib/field-reports/checklist-photo-constants.ts");

    expect(constants).toContain("MAX_CHECKLIST_ITEM_PHOTOS = 3");
    expect(validation).toContain("DEFECT_MISSING_PHOTO");
    expect(validation).not.toContain('status === "OK"');
  });

  it("§17.4 validation — UNCHECKED requires note to close", () => {
    const validation = readUiSource("lib/field-reports/checklist-close-validation.ts");
    const close = readUiSource("lib/field-reports/supervision-close.ts");

    expect(validation).toContain("UNCHECKED_MISSING_NOTE");
    expect(close).toContain("validateChecklistForClose");
    expect(close).toContain("prepareSupervisionReportForClose");
  });

  it("§17.5 defect finding + portal only after publish", () => {
    const defectLine = readUiSource("lib/field-reports/checklist-defect-to-line.ts");
    const page = readUiSource("app/(dashboard)/field-reports/[id]/page.tsx");
    const visitService = readRepoSource("app/services/field_visit_report_service.py");

    expect(defectLine).toContain("buildDefectFindingLine");
    expect(defectLine).toContain("applySupervisionDefectLinesToReport");
    expect(page).toContain("prepareSupervisionReportForClose");
    expect(page).toContain("buildSupervisionClosePreview");
    expect(visitService).toContain("IssueVisibility.DRAFT");
    expect(visitService).toContain("def publish_report");
  });

  it("§17.6 offline — prep bundle, local close, PDF without network", () => {
    const offlineTypes = readUiSource("lib/field-reports/offline-store-types.ts");
    const closeLocal = readUiSource("lib/field-reports/close-local-visit-report.ts");
    const pdfGenerator = readUiSource("lib/field-reports/pdf/generate-visit-report-pdf.ts");
    const backend = readRepoSource("app/services/field_visit_report_service.py");

    expect(offlineTypes).toContain("apartments_by_project");
    expect(offlineTypes).toContain("supervision_catalog");
    expect(closeLocal).toContain("finishLocalVisitReportWithPdf");
    expect(closeLocal).toContain("generateVisitReportPdf");
    expect(pdfGenerator).toContain("resolveChecklistPhotos");
    expect(backend).toContain("apartments_by_project");
    expect(backend).toContain("supervision_catalog");
  });

  it("§17.7 compatibility — legacy checklist and findings unchanged", () => {
    const renderBlocks = readUiSource("lib/field-reports/pdf/render-blocks.ts");
    const normalize = readUiSource("lib/field-reports/schema/normalize.ts");
    const migrate = readUiSource(
      "lib/field-reports/schema/migrate-legacy-finishing-blocks.ts"
    );

    expect(renderBlocks).toContain('case "checklist"');
    expect(renderBlocks).toContain('case "findings_table"');
    expect(renderBlocks).toContain('case "progress_table"');
    expect(normalize).toContain('case "checklist"');
    expect(migrate).toContain('kind === "checklist"');
    expect(migrate).toContain('kind === "supervision_checklist"');
  });

  it("§16.I — supervision_meta registered in backend KNOWN_HEADER_FIELD_KEYS", () => {
    const schema = readRepoSource("app/schemas/field_report_document.py");
    const schemaTest = readRepoSource("tests/test_field_report_document_schema.py");

    expect(schema).toContain('"supervision_meta"');
    expect(schemaTest).toContain("test_known_header_keys_include_supervision_meta");
  });

  it("wires full offline close path on field-reports/[id] page", () => {
    const page = readUiSource("app/(dashboard)/field-reports/[id]/page.tsx");
    const editor = readUiSource("components/field-reports/VisitReportEditor.tsx");

    expect(page).toContain("finishLocalVisitReportWithPdf");
    expect(page).toContain("prepareSupervisionReportForClose");
    expect(page).toContain("FinishReportDialog");
    expect(editor).toContain("SupervisionChecklistEditor");
  });
});
