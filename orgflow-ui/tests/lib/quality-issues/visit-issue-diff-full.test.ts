import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  buildProjectVisitIssueDiffSummaryRow,
  formatProjectVisitDiffVisitLabel,
  summarizeProjectVisitDiffRows,
} from "@/lib/quality-issues/project-visit-issue-diff";
import {
  parseQualityIssueVisitDiffResponse,
  type QualityIssueVisitDiffResponse,
} from "@/lib/quality-issues/types";
import {
  buildVisitIssueDiffBuckets,
  formatVisitIssueDiffSummary,
  shouldShowVisitIssueDiff,
  visitIssueDiffHasChanges,
} from "@/lib/quality-issues/visit-issue-diff";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

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

const VISIT_TWO_DIFF_BODY = {
  project_id: "proj-1",
  report_id: "report-2",
  new: [
    {
      issue: { ...SAMPLE_ISSUE, id: "issue-new", title: "חדש" },
      line_id: "line-new",
      category: "new",
    },
  ],
  closed: [
    {
      issue: { ...SAMPLE_ISSUE, id: "issue-closed", status: "CLOSED" },
      line_id: "line-closed",
      category: "closed",
    },
  ],
  still_open: [
    {
      issue: { ...SAMPLE_ISSUE, id: "issue-open", title: "פתוח" },
      line_id: "line-open",
      category: "still_open",
    },
  ],
  recurring: [
    {
      issue: {
        ...SAMPLE_ISSUE,
        id: "issue-recur",
        status: "REOPENED",
        recurrence_count: 1,
      },
      line_id: "line-recur",
      category: "recurring",
    },
  ],
  total_new: 1,
  total_closed: 1,
  total_still_open: 1,
  total_recurring: 1,
};

describe("visit issue diff full (2.3.5)", () => {
  it("parses visit diff API response with all four buckets", () => {
    const diff = parseQualityIssueVisitDiffResponse(VISIT_TWO_DIFF_BODY);

    expect(diff.report_id).toBe("report-2");
    expect(diff.total_new).toBe(1);
    expect(diff.new[0]?.category).toBe("new");
    expect(diff.closed[0]?.issue.status).toBe("CLOSED");
    expect(diff.still_open[0]?.issue.title).toBe("פתוח");
    expect(diff.recurring[0]?.issue.recurrence_count).toBe(1);
  });

  it("formats visit diff summary text for report and project views", () => {
    const diff = parseQualityIssueVisitDiffResponse(VISIT_TWO_DIFF_BODY);

    expect(formatVisitIssueDiffSummary(diff)).toBe(
      "1 חדש · 1 נסגר · 1 עדיין פתוח · 1 חוזר"
    );
    expect(visitIssueDiffHasChanges(diff)).toBe(true);
    expect(buildVisitIssueDiffBuckets(diff).map((bucket) => bucket.total)).toEqual([
      1, 1, 1, 1,
    ]);
  });

  it("aggregates project visit rows from parsed diffs", () => {
    const diff = parseQualityIssueVisitDiffResponse(VISIT_TWO_DIFF_BODY);
    const row = buildProjectVisitIssueDiffSummaryRow(
      {
        id: "report-2",
        project_id: "proj-1",
        visit_date: "2026-06-07",
        visit_type_label_he: "גמר",
        status: "CLOSED",
        status_label_he: "סגור",
      },
      diff
    );

    const aggregate = summarizeProjectVisitDiffRows([row]);

    expect(formatProjectVisitDiffVisitLabel(row)).toContain("גמר");
    expect(row.summary_text).toBe("1 חדש · 1 נסגר · 1 עדיין פתוח · 1 חוזר");
    expect(aggregate.visit_count).toBe(1);
    expect(aggregate.visits_with_changes).toBe(1);
    expect(aggregate.totals.map((bucket) => bucket.total)).toEqual([1, 1, 1, 1]);
  });

  it("hides diff panel for editable reports and shows for closed visits", () => {
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
  });

  it("reports empty diff without changes", () => {
    const empty: QualityIssueVisitDiffResponse = {
      project_id: "proj-1",
      report_id: "report-1",
      new: [],
      closed: [],
      still_open: [],
      recurring: [],
      total_new: 0,
      total_closed: 0,
      total_still_open: 0,
      total_recurring: 0,
    };

    expect(formatVisitIssueDiffSummary(empty)).toBe(
      "אין שינויי ליקויים בביקור זה"
    );
    expect(visitIssueDiffHasChanges(empty)).toBe(false);
    expect(summarizeProjectVisitDiffRows([]).visit_count).toBe(0);
  });
});

describe("visit issue diff full UI gate (2.3.5)", () => {
  it("wires API, report diff panel, and project summary for section 2.3", () => {
    const apiClient = readUiSource("lib/quality-issues/api.ts");
    const types = readUiSource("lib/quality-issues/types.ts");
    const visitHelpers = readUiSource("lib/quality-issues/visit-issue-diff.ts");
    const projectHelpers = readUiSource(
      "lib/quality-issues/project-visit-issue-diff.ts"
    );
    const projectVisits = readUiSource("lib/field-reports/project-visits.ts");
    const reportPanel = readUiSource(
      "components/quality-issues/VisitReportIssueDiffPanel.tsx"
    );
    const projectSummary = readUiSource(
      "components/quality-issues/ProjectVisitIssueDiffSummary.tsx"
    );
    const reportPage = readUiSource(
      "app/(dashboard)/field-reports/[id]/page.tsx"
    );
    const projectPage = readUiSource(
      "app/(dashboard)/projects/[id]/page.tsx"
    );

    expect(apiClient).toContain("getProjectVisitIssueDiff");
    expect(types).toContain("parseQualityIssueVisitDiffResponse");
    expect(visitHelpers).toContain("formatVisitIssueDiffSummary");
    expect(projectHelpers).toContain("loadProjectVisitIssueDiffSummaries");
    expect(projectVisits).toContain("listProjectFieldVisitReports");
    expect(reportPanel).toContain("getProjectVisitIssueDiff");
    expect(projectSummary).toContain("summarizeProjectVisitDiffRows");
    expect(reportPage).toContain("VisitReportIssueDiffPanel");
    expect(projectPage).toContain("ProjectVisitIssueDiffSummary");
  });
});
