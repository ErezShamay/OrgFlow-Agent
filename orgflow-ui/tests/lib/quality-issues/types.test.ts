import { describe, expect, it } from "vitest";

import {
  DEFAULT_QUALITY_ISSUE_LIST_QUERY,
  EVENT_TYPES_REQUIRING_ACTOR,
  EVENT_TYPES_REQUIRING_REPORT,
  QUALITY_ISSUE_EVENT_TYPES,
  QUALITY_ISSUE_SEVERITIES,
  QUALITY_ISSUE_STATUSES,
  buildMatchKey,
  buildMaterializationKey,
  buildQualityIssueListQueryParams,
  compareSeverity,
  deriveIssueTitle,
  findingRowQualifiesForMaterialization,
  isTerminalIssueStatus,
  isValidStatusTransition,
  normalizeCatalogSeverity,
  parseQualityIssue,
  parseQualityIssueDetailResponse,
  parseQualityIssueEvent,
  parseQualityIssueListResponse,
  parseQualityIssueOpenListResponse,
  parseQualityPortfolioSummaryResponse,
  preferredEventTypeForTransition,
  resolveIssueSeverity,
  withCreateRequestDefaults,
} from "@/lib/quality-issues/types";

describe("quality issue types (spec 0.1)", () => {
  it("defines severity and status enums matching backend", () => {
    expect(QUALITY_ISSUE_SEVERITIES).toEqual([
      "CRITICAL",
      "HIGH",
      "MEDIUM",
      "LOW",
    ]);
    expect(QUALITY_ISSUE_STATUSES).toEqual([
      "OPEN",
      "IN_REMEDIATION",
      "PENDING_VERIFICATION",
      "CLOSED",
      "REOPENED",
    ]);
  });

  it("normalizes catalog severity values", () => {
    expect(normalizeCatalogSeverity("Critical")).toBe("CRITICAL");
    expect(normalizeCatalogSeverity(" low ")).toBe("LOW");
    expect(normalizeCatalogSeverity(null)).toBeNull();
    expect(normalizeCatalogSeverity("invalid")).toBeNull();
  });

  it("builds materialization and match keys", () => {
    expect(buildMaterializationKey("r1", "l1")).toBe("r1:l1");
    expect(
      buildMatchKey({
        location: "  דירה  3  ",
        trade: "אינסטלציה",
        group_key: "BATH",
      })
    ).toBe("דירה 3|אינסטלציה|bath");
  });
});

describe("quality issue events (spec 0.2)", () => {
  it("defines event types matching backend", () => {
    expect(QUALITY_ISSUE_EVENT_TYPES).toEqual([
      "DETECTED",
      "LINKED",
      "REMEDIATION_SUBMITTED",
      "VERIFIED_CLOSED",
      "REOPENED",
      "STATUS_CHANGED",
    ]);
  });

  it("marks actor and report requirements per event type", () => {
    expect(EVENT_TYPES_REQUIRING_ACTOR.has("VERIFIED_CLOSED")).toBe(true);
    expect(EVENT_TYPES_REQUIRING_ACTOR.has("DETECTED")).toBe(false);
    expect(EVENT_TYPES_REQUIRING_REPORT.has("DETECTED")).toBe(true);
    expect(EVENT_TYPES_REQUIRING_REPORT.has("STATUS_CHANGED")).toBe(false);
  });

  it("maps status transitions to preferred event types", () => {
    expect(preferredEventTypeForTransition(null, "OPEN")).toBe("DETECTED");
    expect(preferredEventTypeForTransition("CLOSED", "REOPENED")).toBe(
      "REOPENED"
    );
    expect(
      preferredEventTypeForTransition(
        "IN_REMEDIATION",
        "PENDING_VERIFICATION"
      )
    ).toBe("REMEDIATION_SUBMITTED");
    expect(
      preferredEventTypeForTransition("PENDING_VERIFICATION", "CLOSED")
    ).toBe("VERIFIED_CLOSED");
    expect(preferredEventTypeForTransition("OPEN", "IN_REMEDIATION")).toBe(
      "STATUS_CHANGED"
    );
  });
});

describe("quality issue domain helpers (spec 0.1)", () => {
  it("ranks severity and detects terminal status", () => {
    expect(compareSeverity("CRITICAL", "LOW")).toBeGreaterThan(0);
    expect(compareSeverity("LOW", "CRITICAL")).toBeLessThan(0);
    expect(isTerminalIssueStatus("CLOSED")).toBe(true);
    expect(isTerminalIssueStatus("OPEN")).toBe(false);
  });

  it("validates allowed status transitions", () => {
    expect(isValidStatusTransition("OPEN", "IN_REMEDIATION")).toBe(true);
    expect(isValidStatusTransition("CLOSED", "OPEN")).toBe(false);
    expect(isValidStatusTransition("OPEN", "OPEN")).toBe(true);
  });

  it("resolves severity from catalog or row values", () => {
    expect(
      resolveIssueSeverity({ catalogSeverity: "High", rowSeverity: "Low" })
    ).toBe("HIGH");
    expect(resolveIssueSeverity({ rowSeverity: "invalid" })).toBe("MEDIUM");
  });

  it("derives issue titles per spec rules", () => {
    expect(
      deriveIssueTitle({ catalogIssueName: "  סדק בטיח  " })
    ).toBe("סדק בטיח");
    expect(
      deriveIssueTitle({
        description: "x".repeat(90),
        location: "דירה 1",
      })
    ).toHaveLength(80);
    expect(
      deriveIssueTitle({ location: "דירה 1", trade: "אינסטלציה" })
    ).toBe("דירה 1 - אינסטלציה");
    expect(deriveIssueTitle({})).toBe("ליקוי ללא תיאור");
  });

  it("checks materialization eligibility for finding rows", () => {
    expect(
      findingRowQualifiesForMaterialization({ description: "  " })
    ).toBe(false);
    expect(
      findingRowQualifiesForMaterialization({ catalogIssueId: "STR-001" })
    ).toBe(true);
    expect(
      findingRowQualifiesForMaterialization({ photoIds: ["p1"] })
    ).toBe(true);
  });
});

describe("quality issue API types (1.3.1)", () => {
  const now = "2026-06-09T12:00:00.000Z";

  const sampleIssueRow = {
    id: "issue-1",
    organization_id: "org-1",
    project_id: "proj-1",
    title: "נזילה",
    severity: "HIGH",
    status: "OPEN",
    first_seen_report_id: "report-1",
    first_seen_at: now,
    last_seen_report_id: "report-1",
    last_seen_at: now,
    materialization_key: "report-1:line-1",
    photo_ids: null,
    recurrence_count: 0,
  };

  it("parses issue rows and normalizes photo_ids", () => {
    const issue = parseQualityIssue(sampleIssueRow);
    expect(issue.photo_ids).toEqual([]);
    expect(issue.severity).toBe("HIGH");
    expect(issue.status).toBe("OPEN");
  });

  it("parses issue events with empty payload fallback", () => {
    const event = parseQualityIssueEvent({
      id: "event-1",
      issue_id: "issue-1",
      event_type: "DETECTED",
      report_id: "report-1",
      payload: null,
    });
    expect(event.event_type).toBe("DETECTED");
    expect(event.payload).toEqual({});
  });

  it("parses open issues list API response", () => {
    const openList = parseQualityIssueOpenListResponse({
      project_id: "proj-1",
      total: 1,
      items: [sampleIssueRow],
    });
    expect(openList.items).toHaveLength(1);
    expect(openList.total).toBe(1);
  });

  it("parses list and detail API responses", () => {
    const list = parseQualityIssueListResponse({
      project_id: "proj-1",
      total: 1,
      limit: 50,
      offset: 0,
      items: [sampleIssueRow],
    });
    expect(list.items).toHaveLength(1);
    expect(list.total).toBe(1);

    const detail = parseQualityIssueDetailResponse({
      issue: sampleIssueRow,
      events: [
        {
          id: "event-1",
          issue_id: "issue-1",
          event_type: "DETECTED",
          report_id: "report-1",
        },
      ],
    });
    expect(detail.issue.id).toBe("issue-1");
    expect(detail.events).toHaveLength(1);
  });

  it("parses portfolio quality summary response", () => {
    const summary = parseQualityPortfolioSummaryResponse({
      organization_id: "org-1",
      total_open: 3,
      total_open_critical: 1,
      critical_open_over_14_days: 0,
      average_open_days: 5.5,
      closed_within_30_days_percent: 80,
      projects: [
        {
          project_id: "proj-1",
          project_name: "האורנים",
          open_total: 3,
          open_critical: 1,
          critical_open_over_14_days: 1,
          average_open_days: 5.5,
        },
      ],
    });
    expect(summary.projects[0]?.project_name).toBe("האורנים");
    expect(summary.projects[0]?.critical_open_over_14_days).toBe(1);
    expect(summary.average_open_days).toBe(5.5);
  });

  it("applies create-request defaults for last_seen fields", () => {
    const normalized = withCreateRequestDefaults({
      title: "נזילה",
      first_seen_report_id: "report-1",
      first_seen_line_id: "line-1",
      first_seen_at: now,
      materialization_key: "report-1:line-1",
    });
    expect(normalized.last_seen_report_id).toBe("report-1");
    expect(normalized.last_seen_line_id).toBe("line-1");
    expect(normalized.last_seen_at).toBe(now);
    expect(normalized.severity).toBe("MEDIUM");
    expect(normalized.photo_ids).toEqual([]);
  });

  it("builds list query params for API client", () => {
    const params = buildQualityIssueListQueryParams({
      status: ["OPEN", "REOPENED"],
      severity: ["CRITICAL"],
      trade: "אינסטלציה",
      search: "נזילה",
      limit: 25,
      offset: 10,
    });
    expect(params.get("limit")).toBe("25");
    expect(params.get("offset")).toBe("10");
    expect(params.getAll("status")).toEqual(["OPEN", "REOPENED"]);
    expect(params.get("trade")).toBe("אינסטלציה");
    expect(params.get("search")).toBe("נזילה");
  });

  it("exposes default list query constants", () => {
    expect(DEFAULT_QUALITY_ISSUE_LIST_QUERY).toEqual({
      limit: 50,
      offset: 0,
    });
  });
});
