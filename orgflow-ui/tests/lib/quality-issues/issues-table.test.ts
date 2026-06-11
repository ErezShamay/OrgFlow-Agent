import { describe, expect, it } from "vitest";

import {
  ISSUES_TABLE_COLUMN_LABELS,
  buildIssueTableRow,
  buildIssuesTableRows,
  formatIssueDate,
  formatIssueLocation,
  formatIssuePhotoCount,
  formatIssueTrade,
  formatIssuesTableSummary,
  severityBadgeVariant,
  statusBadgeVariant,
} from "@/components/quality-issues/IssuesTable";
import type { QualityIssue } from "@/lib/quality-issues/types";

const SAMPLE_ISSUE: QualityIssue = {
  id: "issue-1",
  organization_id: "org-1",
  project_id: "proj-1",
  title: "נזילה בחדר רחצה",
  description: "נזילה מתמשכת",
  location: "דירה 3",
  trade: "אינסטלציה",
  severity: "HIGH",
  status: "OPEN",
  first_seen_report_id: "report-1",
  first_seen_at: "2026-06-09T12:00:00.000Z",
  last_seen_report_id: "report-1",
  last_seen_at: "2026-06-09T12:00:00.000Z",
  recurrence_count: 0,
  photo_ids: ["p1", "p2"],
  materialization_key: "report-1:line-1",
};

describe("IssuesTable helpers (1.3.4)", () => {
  it("formats issue dates for Hebrew locale display", () => {
    expect(formatIssueDate(null)).toBe("-");
    expect(formatIssueDate("2026-06-09T12:00:00.000Z")).toMatch(/\d/);
  });

  it("maps severity and status to badge variants", () => {
    expect(severityBadgeVariant("CRITICAL")).toBe("danger");
    expect(severityBadgeVariant("LOW")).toBe("neutral");
    expect(statusBadgeVariant("CLOSED")).toBe("success");
    expect(statusBadgeVariant("OPEN")).toBe("warning");
    expect(statusBadgeVariant("IN_REMEDIATION")).toBe("info");
  });

  it("formats location, trade, and photo count cells", () => {
    expect(formatIssueLocation("  דירה 3  ")).toBe("דירה 3");
    expect(formatIssueLocation(null)).toBe("-");
    expect(formatIssueTrade("אינסטלציה")).toBe("אינסטלציה");
    expect(formatIssueTrade("")).toBe("-");
    expect(formatIssuePhotoCount(["p1", "p2"])).toBe("2 תמונות");
    expect(formatIssuePhotoCount([])).toBe("-");
  });

  it("builds table summary for full and paginated lists", () => {
    expect(formatIssuesTableSummary(5)).toBe("5 ליקויים");
    expect(formatIssuesTableSummary(5, 5)).toBe("5 ליקויים");
    expect(formatIssuesTableSummary(25, 120)).toBe(
      "מציג 25 מתוך 120 ליקויים"
    );
  });
});

describe("IssuesTable row rendering (1.3.8)", () => {
  it("defines Hebrew column headers for the table", () => {
    expect(ISSUES_TABLE_COLUMN_LABELS).toEqual([
      "ליקוי",
      "סטטוס",
      "חומרה",
      "מיקום",
      "מלאכה",
      "גילוי ראשון",
      "תמונות",
    ]);
  });

  it("builds a display row with status, severity, location, trade, and date", () => {
    const row = buildIssueTableRow(SAMPLE_ISSUE, { projectId: "proj-1" });

    expect(row).toMatchObject({
      id: "issue-1",
      href: "/projects/proj-1/issues/issue-1",
      title: "נזילה בחדר רחצה",
      description: "נזילה מתמשכת",
      statusLabel: "פתוח",
      statusVariant: "warning",
      severityLabel: "גבוה",
      severityVariant: "warning",
      location: "דירה 3",
      trade: "אינסטלציה",
      photoCountLabel: "2 תמונות",
      photoCount: 2,
      hasPhotos: true,
    });
    expect(row.firstSeenAt).toMatch(/\d/);
  });

  it("builds rows for every issue in list order", () => {
    const rows = buildIssuesTableRows(
      [
        SAMPLE_ISSUE,
        {
          ...SAMPLE_ISSUE,
          id: "issue-2",
          title: "סדק",
          status: "CLOSED",
          severity: "CRITICAL",
          location: null,
          trade: null,
          photo_ids: [],
        },
      ],
      { projectId: "proj-1" }
    );

    expect(rows).toHaveLength(2);
    expect(rows[1]?.statusLabel).toBe("סגור");
    expect(rows[1]?.severityLabel).toBe("קריטי");
    expect(rows[1]?.location).toBe("-");
    expect(rows[1]?.trade).toBe("-");
    expect(rows[1]?.photoCountLabel).toBe("-");
    expect(rows[1]?.hasPhotos).toBe(false);
  });
});
