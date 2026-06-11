import { afterEach, describe, expect, it, vi } from "vitest";

import {
  QualityIssueApiError,
  buildIssuePath,
  buildPortfolioQualitySummaryPath,
  buildProjectIssuesPath,
  buildProjectOpenIssuesPath,
  buildProjectSuggestMatchesPath,
  buildProjectVisitIssueDiffPath,
  createProjectQualityIssue,
  getPortfolioQualitySummary,
  getProjectVisitIssueDiff,
  getQualityIssueDetail,
  listProjectOpenQualityIssues,
  listProjectQualityIssues,
  suggestProjectQualityIssueMatches,
  updateQualityIssue,
} from "@/lib/quality-issues/api";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

const NOW = "2026-06-09T12:00:00.000Z";

const SAMPLE_ISSUE = {
  id: "issue-1",
  organization_id: "org-1",
  project_id: "proj-1",
  title: "נזילה",
  severity: "HIGH",
  status: "OPEN",
  first_seen_report_id: "report-1",
  first_seen_at: NOW,
  last_seen_report_id: "report-1",
  last_seen_at: NOW,
  materialization_key: "report-1:line-1",
  photo_ids: [],
  recurrence_count: 0,
};

function jsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => body,
  } as Response;
}

describe("quality issues API paths (1.3.2)", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("builds encoded API paths", () => {
    expect(buildProjectIssuesPath("proj 1")).toBe("/projects/proj%201/issues");
    expect(buildProjectOpenIssuesPath("proj-1")).toBe(
      "/projects/proj-1/issues/open"
    );
    expect(buildProjectSuggestMatchesPath("proj-1")).toBe(
      "/projects/proj-1/issues/suggest-matches"
    );
    expect(buildIssuePath("issue/2")).toBe("/issues/issue%2F2");
    expect(buildPortfolioQualitySummaryPath()).toBe(
      "/portfolio/quality-summary"
    );
    expect(buildProjectVisitIssueDiffPath("proj-1", "report 2")).toBe(
      "/projects/proj-1/visits/report%202/issue-diff"
    );
  });

  it("loads visit issue diff for a closed report", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({
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
      })
    );

    const diff = await getProjectVisitIssueDiff("proj-1", "report-2");

    expect(apiFetch).toHaveBeenCalledWith(
      "/projects/proj-1/visits/report-2/issue-diff"
    );
    expect(diff.report_id).toBe("report-2");
    expect(diff.total_new).toBe(0);
  });

  it("lists project issues with severity and search query params", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({
        project_id: "proj-1",
        total: 0,
        limit: 25,
        offset: 10,
        items: [],
      })
    );

    await listProjectQualityIssues("proj-1", {
      severity: ["CRITICAL", "HIGH"],
      search: "נזילה",
      limit: 25,
      offset: 10,
    });

    expect(apiFetch).toHaveBeenCalledWith(
      "/projects/proj-1/issues?limit=25&offset=10&severity=CRITICAL&severity=HIGH&search=%D7%A0%D7%96%D7%99%D7%9C%D7%94"
    );
  });

  it("lists open project issues for field-report matching", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({
        project_id: "proj-1",
        total: 1,
        items: [SAMPLE_ISSUE],
      })
    );

    const result = await listProjectOpenQualityIssues("proj-1");

    expect(result.total).toBe(1);
    expect(result.items[0]?.status).toBe("OPEN");
    expect(apiFetch).toHaveBeenCalledWith("/projects/proj-1/issues/open");
  });

  it("suggests matching open issues for a finding row", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({
        project_id: "proj-1",
        match_key: "דירה 3|אינסטלציה|bath",
        total: 1,
        candidates: [
          {
            issue: SAMPLE_ISSUE,
            match_key: "דירה 3|אינסטלציה|bath",
            score: 1,
          },
        ],
      })
    );

    const result = await suggestProjectQualityIssueMatches("proj-1", {
      location: "דירה 3",
      trade: "אינסטלציה",
      group_key: "bath",
    });

    expect(result.total).toBe(1);
    expect(result.candidates[0]?.issue.id).toBe("issue-1");
    expect(result.candidates[0]?.score).toBe(1);
    expect(apiFetch).toHaveBeenCalledWith(
      "/projects/proj-1/issues/suggest-matches",
      {
        method: "POST",
        body: JSON.stringify({
          location: "דירה 3",
          trade: "אינסטלציה",
          group_key: "bath",
        }),
      }
    );
  });

  it("lists project issues with query params", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({
        project_id: "proj-1",
        total: 1,
        limit: 50,
        offset: 0,
        items: [SAMPLE_ISSUE],
      })
    );

    const result = await listProjectQualityIssues("proj-1", {
      status: ["OPEN"],
      trade: "אינסטלציה",
    });

    expect(result.items).toHaveLength(1);
    expect(result.items[0]?.title).toBe("נזילה");
    expect(apiFetch).toHaveBeenCalledWith(
      "/projects/proj-1/issues?limit=50&offset=0&status=OPEN&trade=%D7%90%D7%99%D7%A0%D7%A1%D7%98%D7%9C%D7%A6%D7%99%D7%94"
    );
  });

  it("creates a project issue with last_seen defaults", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(jsonResponse(SAMPLE_ISSUE));

    const issue = await createProjectQualityIssue("proj-1", {
      title: "נזילה",
      first_seen_report_id: "report-1",
      first_seen_line_id: "line-1",
      first_seen_at: NOW,
      materialization_key: "report-1:line-1",
    });

    expect(issue.id).toBe("issue-1");

    const callArgs = vi.mocked(apiFetch).mock.calls[0]?.[1];
    expect(callArgs?.method).toBe("POST");
    expect(JSON.parse(String(callArgs?.body))).toEqual({
      title: "נזילה",
      first_seen_report_id: "report-1",
      first_seen_line_id: "line-1",
      first_seen_at: NOW,
      last_seen_report_id: "report-1",
      last_seen_line_id: "line-1",
      last_seen_at: NOW,
      materialization_key: "report-1:line-1",
      severity: "MEDIUM",
      photo_ids: [],
    });
  });

  it("loads issue detail with events", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({
        issue: SAMPLE_ISSUE,
        events: [
          {
            id: "event-1",
            issue_id: "issue-1",
            event_type: "DETECTED",
            report_id: "report-1",
            payload: {},
          },
        ],
      })
    );

    const detail = await getQualityIssueDetail("issue-1");

    expect(detail.issue.id).toBe("issue-1");
    expect(detail.events).toHaveLength(1);
    expect(apiFetch).toHaveBeenCalledWith("/issues/issue-1");
  });

  it("updates an issue via PATCH", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({
        ...SAMPLE_ISSUE,
        status: "CLOSED",
      })
    );

    const issue = await updateQualityIssue("issue-1", {
      status: "CLOSED",
    });

    expect(issue.status).toBe("CLOSED");
    expect(apiFetch).toHaveBeenCalledWith("/issues/issue-1", {
      method: "PATCH",
      body: JSON.stringify({ status: "CLOSED" }),
    });
  });

  it("loads portfolio quality summary", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({
        organization_id: "org-1",
        total_open: 2,
        total_open_critical: 1,
        critical_open_over_14_days: 0,
        average_open_days: 4,
        closed_within_30_days_percent: 75,
        projects: [
          {
            project_id: "proj-1",
            project_name: "האורנים",
            open_total: 2,
            open_critical: 1,
          },
        ],
      })
    );

    const summary = await getPortfolioQualitySummary();

    expect(summary.total_open).toBe(2);
    expect(summary.projects[0]?.project_name).toBe("האורנים");
    expect(apiFetch).toHaveBeenCalledWith("/portfolio/quality-summary");
  });

  it("throws QualityIssueApiError when list request fails", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({ detail: "שגיאת שרת" }, false, 500)
    );

    await expect(listProjectQualityIssues("proj-1")).rejects.toMatchObject({
      name: "QualityIssueApiError",
      status: 500,
      message: "שגיאת שרת",
    });
  });

  it("throws QualityIssueApiError on failed responses", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({ detail: "מעבר סטטוס לא חוקי" }, false, 400)
    );

    await expect(
      updateQualityIssue("issue-1", { status: "CLOSED" })
    ).rejects.toMatchObject({
      name: "QualityIssueApiError",
      status: 400,
      message: "מעבר סטטוס לא חוקי",
    } satisfies Partial<QualityIssueApiError>);
  });
});
