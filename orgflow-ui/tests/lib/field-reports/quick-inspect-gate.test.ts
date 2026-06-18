/**
 * Gate — QuickInspect V/X mode (COMPETITIVE-LAYER-TASKS.md V1).
 * UI only: V→OK, X→DEFECT, menu→NOT_APPLICABLE; weekly_inspection defaults to quick.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  QUICK_INSPECT_STATUS_MAP,
  defaultInspectModeForDocumentType,
  resolveInspectMode,
} from "@/lib/field-reports/quick-inspect";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("quick inspect gate V1", () => {
  it("exposes inspect_mode on SupervisionReportMeta", () => {
    const types = readSource("lib/field-reports/schema/types.ts");

    expect(types).toContain('inspect_mode?: InspectMode');
    expect(types).toContain('"standard"');
    expect(types).toContain('"quick"');
  });

  it("ships QuickInspectToggle and wires it in SupervisionChecklistEditor", () => {
    const togglePath = path.join(
      UI_ROOT,
      "components/field-reports/supervision/QuickInspectToggle.tsx"
    );
    const editor = readSource("components/field-reports/SupervisionChecklistEditor.tsx");

    expect(existsSync(togglePath)).toBe(true);
    expect(editor).toContain("QuickInspectToggle");
    expect(editor).toContain('inspectMode === "quick"');
    expect(editor).toContain("CHECKLIST_ITEM_STATUS_OPTIONS");
  });

  it("passes inspectMode from VisitReportEditor via resolveInspectMode", () => {
    const editor = readSource("components/field-reports/VisitReportEditor.tsx");
    const blocksManager = readSource("components/field-reports/ReportBlocksManager.tsx");

    expect(editor).toContain("resolveInspectMode");
    expect(editor).toContain("inspectMode={inspectMode}");
    expect(blocksManager).toContain("inspectMode?: InspectMode");
  });

  it("defaults weekly_inspection to quick on create", () => {
    const newReport = readSource("lib/field-reports/supervision-new-report.ts");

    expect(newReport).toContain("defaultInspectModeForDocumentType");
    expect(newReport).toContain("inspect_mode:");
  });

  it("maps quick UI actions to existing checklist statuses", () => {
    expect(QUICK_INSPECT_STATUS_MAP.ok).toBe("OK");
    expect(QUICK_INSPECT_STATUS_MAP.defect).toBe("DEFECT");
    expect(QUICK_INSPECT_STATUS_MAP.untouched).toBe("UNCHECKED");
    expect(QUICK_INSPECT_STATUS_MAP.notApplicable).toBe("NOT_APPLICABLE");
  });

  it("resolveInspectMode — weekly_inspection → quick, handover → standard", () => {
    expect(
      resolveInspectMode({
        document_type: "weekly_inspection",
      })
    ).toBe("quick");

    expect(
      resolveInspectMode({
        document_type: "handover_protocol",
      })
    ).toBe("standard");

    expect(
      resolveInspectMode({
        document_type: "weekly_inspection",
        inspect_mode: "standard",
      })
    ).toBe("standard");

    expect(defaultInspectModeForDocumentType("weekly_inspection")).toBe("quick");
    expect(defaultInspectModeForDocumentType("handover_protocol")).toBe(
      "standard"
    );
  });
});
