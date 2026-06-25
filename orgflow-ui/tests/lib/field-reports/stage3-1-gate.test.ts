import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { QUICK_FINDING_PHOTO_TAP_COUNT } from "@/lib/field-reports/quick-finding-photo";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 3.1 gate (quick photo → finding row)", () => {
  it("exposes two-tap quick capture in visit report editor", () => {
    const editor = readUiSource(
      "components/field-reports/VisitReportEditor.tsx"
    );
    const findingsPanel = readUiSource(
      "components/field-reports/ReportFindingsLinesPanel.tsx"
    );
    const quickButton = readUiSource(
      "components/field-reports/QuickFindingPhotoButton.tsx"
    );

    expect(QUICK_FINDING_PHOTO_TAP_COUNT).toBe(2);
    expect(editor).toContain("ReportFindingsLinesPanel");
    expect(editor).toContain("addQuickFindingFromPhoto");
    expect(editor).toContain("buildQuickFindingLinePayload");
    expect(findingsPanel).toContain("QuickFindingPhotoButton");
    expect(quickButton).toContain("צלם ממצא");
    expect(quickButton).toContain("capture: \"environment\"");
  });
});
