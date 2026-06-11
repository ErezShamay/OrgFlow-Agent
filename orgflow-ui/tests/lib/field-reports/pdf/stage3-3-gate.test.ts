import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  PDF_ISSUE_MARKER_COLUMN_HEADER_HE,
  PDF_ISSUE_MARKER_LABELS_HE,
} from "@/lib/field-reports/pdf/pdf-issue-markers";
import { renderFindingsTable } from "@/lib/field-reports/pdf/render-blocks";
import type { FindingsTableBlock } from "@/lib/field-reports/schema/types";

const UI_ROOT = path.resolve(__dirname, "../../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 3.3 gate (PDF issue registry markers)", () => {
  it("renders issue marker column in findings table", () => {
    const block: FindingsTableBlock = {
      id: "findings-1",
      kind: "findings_table",
      title_he: "ממצאים",
      column_preset: "simple",
      rows: [
        {
          id: "line-new",
          description: "סדק",
          sort_order: 0,
        },
        {
          id: "line-closed",
          description: "תיקון",
          sort_order: 1,
        },
      ],
    };

    const markers = new Map<string, string>([
      ["line-new", PDF_ISSUE_MARKER_LABELS_HE.new],
      ["line-closed", PDF_ISSUE_MARKER_LABELS_HE.closed],
    ]);

    const content = renderFindingsTable(block, [], markers);
    const texts = JSON.stringify(content);

    expect(texts).toContain(PDF_ISSUE_MARKER_COLUMN_HEADER_HE);
    expect(texts).toContain("חדש");
    expect(texts).toContain("נסגר");
    expect(texts).not.toContain("פתוח מביקור קודם");
  });

  it("wires issue diff resolution into PDF generation", () => {
    const generator = readUiSource(
      "lib/field-reports/pdf/generate-visit-report-pdf.ts"
    );
    const resolver = readUiSource(
      "lib/field-reports/pdf/resolve-visit-pdf-issue-markers.ts"
    );
    const renderBlocks = readUiSource(
      "lib/field-reports/pdf/render-blocks.ts"
    );

    expect(generator).toContain("resolveVisitPdfIssueMarkers");
    expect(generator).toContain("lineIssueMarkers");
    expect(resolver).toContain("getProjectVisitIssueDiff");
    expect(renderBlocks).toContain("PDF_ISSUE_MARKER_COLUMN_HEADER_HE");
    expect(renderBlocks).toContain("resolvePdfIssueMarkerForLine");
  });
});
