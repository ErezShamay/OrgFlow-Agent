import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildIssuesTableRows,
  formatIssuesTableSummary,
} from "@/components/quality-issues/IssuesTable";
import { listProjectQualityIssues } from "@/lib/quality-issues/api";
import {
  issuesFilterStateToListQuery,
  serializeIssuesFilterKey,
} from "@/lib/quality-issues/filters";
import {
  buildQualityIssueListQueryParams,
  parseQualityIssueListResponse,
} from "@/lib/quality-issues/types";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

const NOW = "2026-06-09T12:00:00.000Z";

const LIST_BODY = {
  project_id: "proj-1",
  total: 2,
  limit: 50,
  offset: 0,
  items: [
    {
      id: "issue-1",
      organization_id: "org-1",
      project_id: "proj-1",
      title: "נזילה",
      location: "דירה 3",
      trade: "אינסטלציה",
      severity: "HIGH",
      status: "OPEN",
      first_seen_report_id: "report-1",
      first_seen_at: NOW,
      last_seen_report_id: "report-1",
      last_seen_at: NOW,
      materialization_key: "report-1:line-1",
      photo_ids: ["p1"],
      recurrence_count: 0,
    },
    {
      id: "issue-2",
      organization_id: "org-1",
      project_id: "proj-1",
      title: "סדק",
      severity: "CRITICAL",
      status: "IN_REMEDIATION",
      first_seen_report_id: "report-2",
      first_seen_at: NOW,
      last_seen_report_id: "report-2",
      last_seen_at: NOW,
      materialization_key: "report-2:line-1",
      photo_ids: [],
      recurrence_count: 0,
    },
  ],
};

function jsonResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => body,
  } as Response;
}

describe("quality issues UI gate (1.3.8)", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("pipes filter state to API query params and cache key", () => {
    const filters = {
      status: "OPEN" as const,
      severity: "HIGH" as const,
      trade: "אינסטלציה",
    };
    const query = issuesFilterStateToListQuery(filters);
    const params = buildQualityIssueListQueryParams(query);

    expect(params.get("status")).toBe("OPEN");
    expect(params.get("severity")).toBe("HIGH");
    expect(params.get("trade")).toBe("אינסטלציה");
    expect(serializeIssuesFilterKey(filters)).toBe(
      "all|all-statuses|OPEN|HIGH|אינסטלציה"
    );
  });

  it("maps API list response into table rows for rendering", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(jsonResponse(LIST_BODY));

    const response = await listProjectQualityIssues("proj-1", {
      status: ["OPEN"],
      severity: ["HIGH", "CRITICAL"],
    });
    const rows = buildIssuesTableRows(response.items, { projectId: "proj-1" });

    expect(response.total).toBe(2);
    expect(rows).toHaveLength(2);
    expect(rows[0]?.title).toBe("נזילה");
    expect(rows[0]?.statusLabel).toBe("פתוח");
    expect(rows[0]?.trade).toBe("אינסטלציה");
    expect(rows[1]?.statusLabel).toBe("בטיפול");
    expect(formatIssuesTableSummary(rows.length, response.total)).toBe(
      "2 ליקויים"
    );
  });

  it("parses list payload before building table rows", () => {
    const parsed = parseQualityIssueListResponse(LIST_BODY);
    const rows = buildIssuesTableRows(parsed.items, { projectId: "proj-1" });

    expect(parsed.project_id).toBe("proj-1");
    expect(rows[0]?.photoCountLabel).toBe("1 תמונות");
    expect(rows[1]?.severityLabel).toBe("קריטי");
  });

  it("surfaces API failures from listProjectQualityIssues", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue(
      jsonResponse({ detail: "אין הרשאה" }, false, 403)
    );

    await expect(listProjectQualityIssues("proj-1")).rejects.toMatchObject({
      name: "QualityIssueApiError",
      status: 403,
    });
  });
});
