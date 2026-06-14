/**
 * Gate — שלב E (field-supervision-checklist-spec §16.E).
 * ולידציה לפני סגירה + DEFECT → שורת ממצא + שילוב FinishReportDialog.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("supervision checklist stage E gate (§16.E)", () => {
  it("checklist-close-validation.ts implements §8.1 rules", () => {
    const validation = readSource(
      "lib/field-reports/checklist-close-validation.ts"
    );

    expect(validation).toContain("export function validateChecklistForClose");
    expect(validation).toContain("DEFECT_MISSING_PHOTO");
    expect(validation).toContain("UNCHECKED_MISSING_NOTE");
  });

  it("checklist-defect-to-line.ts maps DEFECT to finding line", () => {
    const mapper = readSource("lib/field-reports/checklist-defect-to-line.ts");

    expect(mapper).toContain("export function buildDefectFindingLine");
    expect(mapper).toContain("applySupervisionDefectLinesToReport");
    expect(mapper).toContain("group_key");
    expect(mapper).toContain("linked_line_id");
  });

  it("supervision-close.ts prepares report before local close", () => {
    const close = readSource("lib/field-reports/supervision-close.ts");

    expect(close).toContain("prepareSupervisionReportForClose");
    expect(close).toContain("buildSupervisionClosePreview");
    expect(close).toContain("validateChecklistForClose");
  });

  it("FinishReportDialog blocks confirm on blocking_errors", () => {
    const dialog = readSource("components/field-reports/FinishReportDialog.tsx");

    expect(dialog).toContain("blocking_errors");
    expect(dialog).toContain("disabled={loading || Boolean(preview?.blocking_errors?.length)}");
  });

  it("field-reports/[id]/page.tsx integrates supervision close flow", () => {
    const page = readSource("app/(dashboard)/field-reports/[id]/page.tsx");

    expect(page).toContain("prepareSupervisionReportForClose");
    expect(page).toContain("buildSupervisionClosePreview");
    expect(page).toContain("SupervisionCloseValidationError");
  });
});
