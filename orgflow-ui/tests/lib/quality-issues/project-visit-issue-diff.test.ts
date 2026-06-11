import { describe, expect, it, vi } from "vitest";

import type { ProjectFieldVisitListItem } from "@/lib/field-reports/project-visits";
import { listProjectFieldVisitReports } from "@/lib/field-reports/project-visits";
import { getProjectVisitIssueDiff } from "@/lib/quality-issues/api";
import {
  buildProjectVisitIssueDiffSummaryRow,
  formatProjectVisitDiffVisitLabel,
  loadProjectVisitIssueDiffSummaries,
  selectRecentClosedVisitsForDiff,
  summarizeProjectVisitDiffRows,
} from "@/lib/quality-issues/project-visit-issue-diff";
import type { QualityIssueVisitDiffResponse } from "@/lib/quality-issues/types";

vi.mock("@/lib/field-reports/project-visits", () => ({
  listProjectFieldVisitReports: vi.fn(),
}));

vi.mock("@/lib/quality-issues/api", () => ({
  getProjectVisitIssueDiff: vi.fn(),
}));

const NOW = "2026-06-09T12:00:00.000Z";

const VISITS: ProjectFieldVisitListItem[] = [
  {
    id: "report-open",
    project_id: "proj-1",
    visit_date: "2026-06-08",
    visit_type_label_he: "שלד",
    status: "IN_PROGRESS",
  },
  {
    id: "report-2",
    project_id: "proj-1",
    visit_date: "2026-06-07",
    visit_type_label_he: "גמר",
    status: "CLOSED",
    status_label_he: "סגור",
  },
  {
    id: "report-1",
    project_id: "proj-1",
    visit_date: "2026-06-01",
    visit_type_label_he: "שלד",
    status: "LOCKED",
    status_label_he: "נשלח",
  },
];

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

describe("project visit issue diff helpers (2.3.4)", () => {
  it("selects recent closed visits only", () => {
    expect(selectRecentClosedVisitsForDiff(VISITS, 3).map((visit) => visit.id)).toEqual([
      "report-2",
      "report-1",
    ]);
  });

  it("builds summary row with report link and summary text", () => {
    const diff: QualityIssueVisitDiffResponse = {
      ...EMPTY_DIFF,
      total_new: 2,
      total_closed: 1,
    };

    const row = buildProjectVisitIssueDiffSummaryRow(VISITS[1], diff);

    expect(row.report_id).toBe("report-2");
    expect(row.summary_text).toBe("2 חדש · 1 נסגר");
    expect(row.has_changes).toBe(true);
    expect(row.report_href).toBe("/field-reports/report-2");
    expect(formatProjectVisitDiffVisitLabel(row)).toContain("גמר");
  });

  it("aggregates totals across loaded visit rows", () => {
    const rows = [
      buildProjectVisitIssueDiffSummaryRow(VISITS[1], {
        ...EMPTY_DIFF,
        total_new: 1,
        total_still_open: 2,
      }),
      buildProjectVisitIssueDiffSummaryRow(VISITS[2], {
        ...EMPTY_DIFF,
        report_id: "report-1",
        total_closed: 1,
        total_recurring: 1,
      }),
    ];

    const aggregate = summarizeProjectVisitDiffRows(rows);

    expect(aggregate.visit_count).toBe(2);
    expect(aggregate.visits_with_changes).toBe(2);
    expect(aggregate.totals).toEqual([
      { category: "new", label: "חדש", total: 1 },
      { category: "closed", label: "נסגר", total: 1 },
      { category: "still_open", label: "עדיין פתוח", total: 2 },
      { category: "recurring", label: "חוזר", total: 1 },
    ]);
  });

  it("loads visit diff summaries for recent closed reports", async () => {
    vi.mocked(listProjectFieldVisitReports).mockResolvedValue({
      reports: VISITS,
    });
    vi.mocked(getProjectVisitIssueDiff).mockImplementation(
      async (_projectId, reportId) => ({
        ...EMPTY_DIFF,
        report_id: reportId,
        total_new: reportId === "report-2" ? 1 : 0,
      })
    );

    const rows = await loadProjectVisitIssueDiffSummaries("proj-1", {
      limit: 2,
    });

    expect(listProjectFieldVisitReports).toHaveBeenCalledWith("proj-1");
    expect(getProjectVisitIssueDiff).toHaveBeenCalledTimes(2);
    expect(rows.map((row) => row.report_id)).toEqual(["report-2", "report-1"]);
    expect(rows[0].summary_text).toBe("1 חדש");
  });
});
