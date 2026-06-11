import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  buildSuggestMatchesRequestFromFindingRow,
  formatSimilarIssueSummary,
  hasMatchableFindingFields,
} from "@/lib/quality-issues/finding-match-hints";
import { buildMatchKey } from "@/lib/quality-issues/types";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("finding match UI gate (2.1.8)", () => {
  it("wires FindingSimilarIssuesHint through offline-aware resolver", () => {
    const hintSource = readUiSource(
      "components/quality-issues/FindingSimilarIssuesHint.tsx"
    );
    const findingsEditorSource = readUiSource(
      "components/field-reports/ReportFindingsBlockEditor.tsx"
    );
    const lineEditorSource = readUiSource(
      "components/field-reports/ReportLineEditor.tsx"
    );
    const visitEditorSource = readUiSource(
      "components/field-reports/VisitReportEditor.tsx"
    );

    expect(hintSource).toContain("resolveProjectQualityIssueMatches");
    expect(hintSource).toContain("useOffline");
    expect(hintSource).toContain("organizationId");

    expect(findingsEditorSource).toContain("organizationId={organizationId}");
    expect(lineEditorSource).toContain("organizationId={organizationId}");
    expect(lineEditorSource).toContain("reportId={reportId}");
    expect(visitEditorSource).toContain("organizationId={organizationId}");
    expect(visitEditorSource).toContain("reportId={report.server_report_id");
  });

  it("maps finding row fields to match key used by offline cache", () => {
    const fields = {
      location: " דירה 3 ",
      trade: "אינסטלציה",
      group_key: "bath",
      issue_id: "PLB-001",
    };

    expect(hasMatchableFindingFields(fields)).toBe(true);

    const request = buildSuggestMatchesRequestFromFindingRow(fields);
    expect(buildMatchKey(request)).toBe("דירה 3|אינסטלציה|bath");
    expect(
      formatSimilarIssueSummary({
        title: "נזילה",
        location: fields.location,
        trade: fields.trade,
      })
    ).toBe("נזילה - דירה 3 · אינסטלציה");
  });
});
