import { describe, expect, it } from "vitest";

import {
  buildIssueDetailFields,
  formatQualityIssueEventDetails,
  formatQualityIssueEventSummary,
  issueBelongsToProject,
  LIFECYCLE_CLOSURE_EVENT_TYPES,
  sortQualityIssueEvents,
} from "@/lib/quality-issues/issue-detail";
import type { QualityIssue, QualityIssueEvent } from "@/lib/quality-issues/types";

const BASE_ISSUE: QualityIssue = {
  id: "issue-1",
  organization_id: "org-1",
  project_id: "proj-1",
  title: "נזילה",
  description: "נזילה בחדר רחצה",
  location: "דירה 3",
  trade: "אינסטלציה",
  severity: "HIGH",
  status: "OPEN",
  first_seen_report_id: "report-1",
  first_seen_at: "2026-06-09T10:00:00.000Z",
  last_seen_report_id: "report-1",
  last_seen_at: "2026-06-09T10:00:00.000Z",
  recurrence_count: 0,
  photo_ids: ["p1"],
  materialization_key: "report-1:line-1",
};

describe("issue detail helpers (1.3.6)", () => {
  it("checks issue belongs to project", () => {
    expect(issueBelongsToProject(BASE_ISSUE, "proj-1")).toBe(true);
    expect(issueBelongsToProject(BASE_ISSUE, "proj-2")).toBe(false);
  });

  it("builds detail fields from issue", () => {
    const fields = buildIssueDetailFields(BASE_ISSUE);
    expect(fields.some((field) => field.label === "מיקום")).toBe(true);
    expect(fields.some((field) => field.label === "מלאכה")).toBe(true);
    expect(fields.some((field) => field.value.includes("1 תמונות"))).toBe(
      true
    );
  });

  it("prefers linked catalog section over raw standard_ref", () => {
    const fields = buildIssueDetailFields(BASE_ISSUE, {
      issue_id: "QC-MEP-001",
      issue_name_he: "בדיקת לחץ לא בוצעה",
      top_family: "MECHANICAL_ELECTRICAL_SYSTEMS",
      category_id: "PLUMBING",
      category_name_he: "אינסטלציה",
      standard_ref: 'ת"י 1205',
      category_standard_id: 'ת"י 1205',
    });

    const section = fields.find((field) => field.label === "סעיף מפרט");
    expect(section?.value).toContain("אינסטלציה");
    expect(section?.value).toContain("1205");
  });

  it("formats event summaries by type", () => {
    const detected: QualityIssueEvent = {
      id: "e1",
      issue_id: "issue-1",
      event_type: "DETECTED",
      report_id: "report-1",
      payload: {
        materialization_key: "report-1:line-1",
        severity: "HIGH",
        title: "נזילה",
      },
    };

    expect(formatQualityIssueEventSummary(detected)).toBe("התגלות");

    const statusChange: QualityIssueEvent = {
      id: "e2",
      issue_id: "issue-1",
      event_type: "STATUS_CHANGED",
      payload: {
        from_status: "OPEN",
        to_status: "IN_REMEDIATION",
      },
    };

    expect(formatQualityIssueEventSummary(statusChange)).toBe(
      "שינוי סטטוס: פתוח → בטיפול"
    );
  });

  it("sorts events newest first", () => {
    const sorted = sortQualityIssueEvents([
      {
        id: "old",
        issue_id: "issue-1",
        event_type: "DETECTED",
        created_at: "2026-06-01T10:00:00.000Z",
        payload: {
          materialization_key: "r:l",
          severity: "HIGH",
          title: "x",
        },
      },
      {
        id: "new",
        issue_id: "issue-1",
        event_type: "STATUS_CHANGED",
        created_at: "2026-06-09T10:00:00.000Z",
        payload: {
          from_status: "OPEN",
          to_status: "IN_REMEDIATION",
        },
      },
    ]);

    expect(sorted[0]?.id).toBe("new");
  });
});

describe("lifecycle closure events (2.2.5)", () => {
  it("tracks lifecycle closure event types", () => {
    expect(LIFECYCLE_CLOSURE_EVENT_TYPES.has("REMEDIATION_SUBMITTED")).toBe(
      true
    );
    expect(LIFECYCLE_CLOSURE_EVENT_TYPES.has("VERIFIED_CLOSED")).toBe(true);
    expect(LIFECYCLE_CLOSURE_EVENT_TYPES.has("REOPENED")).toBe(true);
  });

  it("formats remediation submitted summary and details", () => {
    const event: QualityIssueEvent = {
      id: "e-rem",
      issue_id: "issue-1",
      event_type: "REMEDIATION_SUBMITTED",
      payload: {
        from_status: "IN_REMEDIATION",
        to_status: "PENDING_VERIFICATION",
        notes: "הוחלפה ברז",
        photo_ids: ["photo-1", "photo-2"],
      },
    };

    expect(formatQualityIssueEventSummary(event)).toBe(
      "הוגש תיקון: בטיפול → ממתין לאימות"
    );
    expect(formatQualityIssueEventDetails(event)).toEqual([
      "הוחלפה ברז",
      "2 תמונות תיקון",
    ]);
  });

  it("formats verified closed summary and notes", () => {
    const event: QualityIssueEvent = {
      id: "e-close",
      issue_id: "issue-1",
      event_type: "VERIFIED_CLOSED",
      report_id: "report-2",
      payload: {
        from_status: "PENDING_VERIFICATION",
        to_status: "CLOSED",
        notes: "תוקן כראוי",
      },
    };

    expect(formatQualityIssueEventSummary(event)).toBe(
      "אושר ונסגר: ממתין לאימות → סגור"
    );
    expect(formatQualityIssueEventDetails(event)).toEqual(["תוקן כראוי"]);
  });

  it("formats reopened summary with recurrence details", () => {
    const event: QualityIssueEvent = {
      id: "e-reopen",
      issue_id: "issue-1",
      event_type: "REOPENED",
      report_id: "report-3",
      payload: {
        from_status: "CLOSED",
        to_status: "REOPENED",
        recurrence_count: 2,
        previous_closed_at: "2026-06-01T10:00:00.000Z",
      },
    };

    expect(formatQualityIssueEventSummary(event)).toBe(
      "נפתח מחדש: סגור → נפתח מחדש"
    );
    expect(formatQualityIssueEventDetails(event)).toEqual([
      "ספירת חזרות: 2",
      expect.stringMatching(/^נסגר קודם:/),
    ]);
  });
});
