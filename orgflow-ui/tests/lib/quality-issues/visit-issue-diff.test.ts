import { describe, expect, it } from "vitest";

import {
  buildVisitIssueDiffBuckets,
  formatVisitIssueDiffSummary,
  isClosedVisitReportStatusForDiff,
  shouldShowVisitIssueDiff,
  visitIssueDiffHasChanges,
} from "@/lib/quality-issues/visit-issue-diff";
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
  last_seen_report_id: "report-1",
  last_seen_at: NOW,
  materialization_key: "report-1:line-1",
  photo_ids: [],
  recurrence_count: 0,
};

const EMPTY_DIFF: QualityIssueVisitDiffResponse = {
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
};

describe("visit issue diff helpers (2.3.3)", () => {
  it("shows diff only for closed reports with project id", () => {
    expect(isClosedVisitReportStatusForDiff("closed")).toBe(true);
    expect(isClosedVisitReportStatusForDiff("IN_PROGRESS")).toBe(false);

    expect(
      shouldShowVisitIssueDiff({
        is_editable: false,
        project_id: "proj-1",
        status: "CLOSED",
      })
    ).toBe(true);

    expect(
      shouldShowVisitIssueDiff({
        is_editable: true,
        project_id: "proj-1",
        status: "IN_PROGRESS",
      })
    ).toBe(false);

    expect(
      shouldShowVisitIssueDiff({
        is_editable: false,
        project_id: "",
        status: "CLOSED",
      })
    ).toBe(false);
  });

  it("builds bucket totals and summary text", () => {
    const diff: QualityIssueVisitDiffResponse = {
      ...EMPTY_DIFF,
      new: [{ issue: SAMPLE_ISSUE, category: "new", line_id: "line-1" }],
      closed: [
        {
          issue: { ...SAMPLE_ISSUE, id: "issue-2", status: "CLOSED" },
          category: "closed",
        },
      ],
      total_new: 1,
      total_closed: 1,
    };

    expect(buildVisitIssueDiffBuckets(diff)).toEqual([
      { category: "new", label: "חדש", total: 1 },
      { category: "closed", label: "נסגר", total: 1 },
      { category: "still_open", label: "עדיין פתוח", total: 0 },
      { category: "recurring", label: "חוזר", total: 0 },
    ]);
    expect(visitIssueDiffHasChanges(diff)).toBe(true);
    expect(formatVisitIssueDiffSummary(diff)).toBe("1 חדש · 1 נסגר");
    expect(formatVisitIssueDiffSummary(EMPTY_DIFF)).toBe(
      "אין שינויי ליקויים בביקור זה"
    );
  });
});
