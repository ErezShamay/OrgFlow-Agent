import { describe, expect, it } from "vitest";

import {
  PDF_ISSUE_MARKER_LABELS_HE,
  buildLineIssueMarkerMapFromVisitDiff,
  resolvePdfIssueMarkerForLine,
} from "@/lib/field-reports/pdf/pdf-issue-markers";
import type { QualityIssueVisitDiffResponse } from "@/lib/quality-issues/types";

const NOW = "2026-06-09T12:00:00.000Z";

const SAMPLE_ISSUE = {
  id: "issue-1",
  organization_id: "org-1",
  project_id: "proj-1",
  title: "נזילה",
  severity: "HIGH" as const,
  status: "OPEN" as const,
  first_seen_report_id: "report-1",
  first_seen_at: NOW,
  last_seen_report_id: "report-2",
  last_seen_at: NOW,
  materialization_key: "report-1:line-1",
  photo_ids: [],
  recurrence_count: 0,
};

function emptyDiff(
  overrides: Partial<QualityIssueVisitDiffResponse> = {}
): QualityIssueVisitDiffResponse {
  return {
    project_id: "proj-1",
    report_id: "report-2",
    new: [],
    closed: [],
    still_open: [],
    recurring: [],
    total_new: 0,
    total_closed: 0,
    total_still_open: 0,
    total_recurring: 0,
    ...overrides,
  };
}

describe("pdf issue markers (3.3)", () => {
  it("uses PDF-specific Hebrew labels", () => {
    expect(PDF_ISSUE_MARKER_LABELS_HE.new).toBe("חדש");
    expect(PDF_ISSUE_MARKER_LABELS_HE.still_open).toBe("פתוח מביקור קודם");
    expect(PDF_ISSUE_MARKER_LABELS_HE.closed).toBe("נסגר");
    expect(PDF_ISSUE_MARKER_LABELS_HE.recurring).toBe("חוזר");
  });

  it("maps visit diff line ids to marker labels", () => {
    const map = buildLineIssueMarkerMapFromVisitDiff(
      emptyDiff({
        new: [
          {
            issue: SAMPLE_ISSUE,
            category: "new",
            line_id: "line-new",
          },
        ],
        still_open: [
          {
            issue: { ...SAMPLE_ISSUE, id: "issue-2" },
            category: "still_open",
            line_id: "line-open",
          },
        ],
        closed: [
          {
            issue: { ...SAMPLE_ISSUE, id: "issue-3", status: "CLOSED" },
            category: "closed",
            line_id: "line-closed",
          },
        ],
        recurring: [
          {
            issue: { ...SAMPLE_ISSUE, id: "issue-4", status: "REOPENED" },
            category: "recurring",
            line_id: "line-recur",
          },
        ],
      })
    );

    expect(map.get("line-new")).toBe("חדש");
    expect(map.get("line-open")).toBe("פתוח מביקור קודם");
    expect(map.get("line-closed")).toBe("נסגר");
    expect(map.get("line-recur")).toBe("חוזר");
  });

  it("resolves marker text for a finding line id", () => {
    const map = buildLineIssueMarkerMapFromVisitDiff(
      emptyDiff({
        closed: [
          {
            issue: { ...SAMPLE_ISSUE, status: "CLOSED" },
            category: "closed",
            line_id: "line-1",
          },
        ],
      })
    );

    expect(resolvePdfIssueMarkerForLine("line-1", map)).toBe("נסגר");
    expect(resolvePdfIssueMarkerForLine("missing", map)).toBe("");
  });
});
