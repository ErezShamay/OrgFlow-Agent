import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  QUICK_FINDING_PHOTO_DESCRIPTION,
  QUICK_FINDING_PHOTO_TAP_COUNT,
  buildQuickFindingLinePayload,
} from "@/lib/field-reports/quick-finding-photo";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 3 gate (quick field visit: photo → row → close)", () => {
  it("exposes two-tap quick capture that creates a materializable finding line", () => {
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

    const payload = buildQuickFindingLinePayload({
      lineId: "line-quick-gate",
      group: { kind: "floor", value: "4" },
    });

    expect(payload.description).toBe(QUICK_FINDING_PHOTO_DESCRIPTION);
    expect(payload.location).toBe("קומה 4");
    expect(payload.group_key).toBe("floor:4");

    expect(editor).toContain("addQuickFindingFromPhoto");
    expect(editor).toContain("buildQuickFindingLinePayload");
    expect(editor).toContain("נוספה שורת ממצא עם תמונה");
    expect(editor).toContain("ReportFindingsLinesPanel");
    expect(findingsPanel).toContain("QuickFindingPhotoButton");
    expect(quickButton).toContain("צלם ממצא");
  });

  it("wires finish/close flow on the field report page", () => {
    const page = readUiSource("app/(dashboard)/field-reports/[id]/page.tsx");
    const primaryActions = readUiSource(
      "components/field-reports/VisitReportPrimaryActions.tsx"
    );
    const finishDialog = readUiSource(
      "components/field-reports/FinishReportDialog.tsx"
    );

    expect(page).toContain("FinishReportDialog");
    expect(page).toContain("confirmFinishReport");
    expect(page).toContain("navigateAfterFinishReport");
    expect(page).toContain("projectFieldReportsListPath");
    expect(page).toContain("VisitReportPrimaryActions");
    expect(page).toContain("/field-reports/visits/");
    expect(page).toContain("/close");

    expect(primaryActions).toContain("onOpenFinishDialog");
    expect(primaryActions).toContain("סיום דוח");

    expect(finishDialog).toContain("אשר וסגור דוח");
  });

  it("documents the end-to-end quick visit sequence", () => {
    const sequence = [
      "QuickFindingPhotoButton",
      "addQuickFindingFromPhoto",
      "saveLinePhotoLocally",
      "VisitReportPrimaryActions",
      "confirmFinishReport",
      "/close",
    ];

    const sources = [
      readUiSource("components/field-reports/VisitReportEditor.tsx"),
      readUiSource("components/field-reports/ReportFindingsLinesPanel.tsx"),
      readUiSource("app/(dashboard)/field-reports/[id]/page.tsx"),
      readFileSync(
        path.resolve(__dirname, "../../../../tests/test_qc_stage3_gate.py"),
        "utf8"
      ),
    ].join("\n");

    for (const marker of sequence) {
      expect(sources).toContain(marker);
    }
  });
});
