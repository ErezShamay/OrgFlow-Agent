import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  buildFindingLineIssueUpdateRequest,
  getFindingLineIssueStatusActions,
} from "@/lib/quality-issues/finding-line-issue-actions";
import { parseQualityIssueVisitDiffResponse } from "@/lib/quality-issues/types";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

const NOW = "2026-06-09T12:00:00.000Z";

const LINKED_ISSUE = {
  id: "issue-v1",
  organization_id: "org-1",
  project_id: "proj-1",
  title: "נזילה בחדר רחצה",
  severity: "MEDIUM" as const,
  status: "OPEN" as const,
  first_seen_report_id: "report-visit-1",
  first_seen_at: NOW,
  last_seen_report_id: "report-visit-2",
  last_seen_at: NOW,
  materialization_key: "report-visit-1:row-v1",
  photo_ids: [],
  recurrence_count: 0,
};

describe("stage 2 gate (visit linking, no duplicates)", () => {
  it("parses visit-2 diff with linked issue in still_open bucket only", () => {
    const diff = parseQualityIssueVisitDiffResponse({
      project_id: "proj-1",
      report_id: "report-visit-2",
      new: [],
      closed: [],
      still_open: [
        {
          issue: LINKED_ISSUE,
          category: "still_open",
          line_id: "line-v2",
        },
      ],
      recurring: [],
      total_new: 0,
      total_closed: 0,
      total_still_open: 1,
      total_recurring: 0,
    });

    expect(diff.total_new).toBe(0);
    expect(diff.total_still_open).toBe(1);
    expect(diff.still_open).toHaveLength(1);
    expect(diff.still_open[0]?.issue.id).toBe("issue-v1");
    expect(diff.still_open[0]?.issue.first_seen_report_id).toBe("report-visit-1");
    expect(diff.still_open[0]?.issue.last_seen_report_id).toBe("report-visit-2");
  });
});

describe("stage 2 gate (visit-2 closure updates registry)", () => {
  it("builds mark-closed request with visit-2 report and line context", () => {
    const action = getFindingLineIssueStatusActions(
      { status: "OPEN" },
      "SUPERVISOR"
    )[0]!;

    expect(
      buildFindingLineIssueUpdateRequest(action, {
        reportId: "report-visit-2",
        lineId: "line-v2",
      })
    ).toEqual({
      status: "CLOSED",
      last_seen_report_id: "report-visit-2",
      last_seen_line_id: "line-v2",
    });
  });

  it("parses visit-2 diff with linked issue in closed bucket after verification", () => {
    const diff = parseQualityIssueVisitDiffResponse({
      project_id: "proj-1",
      report_id: "report-visit-2",
      new: [],
      closed: [
        {
          issue: { ...LINKED_ISSUE, status: "CLOSED" },
          category: "closed",
          line_id: "line-v2",
        },
      ],
      still_open: [],
      recurring: [],
      total_new: 0,
      total_closed: 1,
      total_still_open: 0,
      total_recurring: 0,
    });

    expect(diff.total_closed).toBe(1);
    expect(diff.total_still_open).toBe(0);
    expect(diff.closed[0]?.issue.status).toBe("CLOSED");
    expect(diff.closed[0]?.line_id).toBe("line-v2");
  });
});

describe("stage 2 gate (recurring issue REOPENED)", () => {
  it("builds reopen request with visit-3 report and line context", () => {
    const action = getFindingLineIssueStatusActions(
      { status: "CLOSED" },
      "SUPERVISOR"
    )[0]!;

    expect(action.id).toBe("reopen-issue");
    expect(
      buildFindingLineIssueUpdateRequest(action, {
        reportId: "report-visit-3",
        lineId: "line-v3",
      })
    ).toEqual({
      status: "REOPENED",
      last_seen_report_id: "report-visit-3",
      last_seen_line_id: "line-v3",
    });
  });

  it("parses visit-3 diff with recurring bucket for REOPENED issue", () => {
    const diff = parseQualityIssueVisitDiffResponse({
      project_id: "proj-1",
      report_id: "report-visit-3",
      new: [],
      closed: [],
      still_open: [],
      recurring: [
        {
          issue: {
            ...LINKED_ISSUE,
            status: "REOPENED",
            recurrence_count: 1,
            last_seen_report_id: "report-visit-3",
          },
          category: "recurring",
          line_id: "line-v3",
        },
      ],
      total_new: 0,
      total_closed: 0,
      total_still_open: 0,
      total_recurring: 1,
    });

    expect(diff.total_recurring).toBe(1);
    expect(diff.recurring[0]?.issue.status).toBe("REOPENED");
    expect(diff.recurring[0]?.issue.recurrence_count).toBe(1);
    expect(diff.recurring[0]?.line_id).toBe("line-v3");
  });
});

describe("stage 2 gate UI wiring", () => {
  it("connects visit-2 linking flow without creating duplicate issues", () => {
    const hint = readUiSource(
      "components/quality-issues/FindingSimilarIssuesHint.tsx"
    );
    const findingsEditor = readUiSource(
      "components/field-reports/ReportFindingsBlockEditor.tsx"
    );
    const visitEditor = readUiSource(
      "components/field-reports/VisitReportEditor.tsx"
    );
    const diffPanel = readUiSource(
      "components/quality-issues/VisitReportIssueDiffPanel.tsx"
    );

    expect(hint).toContain("קשר לליקוי");
    expect(hint).toContain("onLinkIssue");
    expect(findingsEditor).toContain("linked_issue_id");
    expect(findingsEditor).toContain("onLinkIssue");
    expect(visitEditor).toContain("linked_issue_id");
    expect(visitEditor).toContain("saveLine");
    expect(diffPanel).toContain("still_open");
    expect(diffPanel).toContain("getProjectVisitIssueDiff");

    const statusActions = readUiSource(
      "components/quality-issues/FindingLinkedIssueStatusActions.tsx"
    );
    expect(statusActions).toContain("buildFindingLineIssueUpdateRequest");
    expect(statusActions).toContain("updateQualityIssue");
    expect(statusActions).toContain("patchOpenIssuesCacheAfterIssueUpdate");
    expect(statusActions).toContain("getFindingLineIssueStatusActions");
    expect(statusActions).toContain("action.label");

    const reopenHelpers = readUiSource(
      "lib/quality-issues/finding-line-issue-actions.ts"
    );
    expect(reopenHelpers).toContain("reopen-issue");
    expect(reopenHelpers).toContain("חזר");
    expect(diffPanel).toContain("recurring");
  });
});
