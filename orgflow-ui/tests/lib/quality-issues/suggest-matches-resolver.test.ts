import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { buildSuggestMatchesRequestFromFindingRow } from "@/lib/quality-issues/finding-match-hints";
import { refreshOpenIssuesCacheForOrganization } from "@/lib/quality-issues/open-issues-offline";
import { resolveProjectQualityIssueMatches } from "@/lib/quality-issues/suggest-matches-resolver";
import type {
  QualityIssue,
  QualityIssueSuggestMatchesResponse,
} from "@/lib/quality-issues/types";

vi.mock("@/lib/quality-issues/api", () => ({
  listProjectOpenQualityIssues: vi.fn(),
  suggestProjectQualityIssueMatches: vi.fn(),
}));

import {
  listProjectOpenQualityIssues,
  suggestProjectQualityIssueMatches,
} from "@/lib/quality-issues/api";

const ORG_ID = "org-suggest-resolver";
const PROJECT_ID = "proj-1";
const mockedSuggestApi = vi.mocked(suggestProjectQualityIssueMatches);
const mockedListOpen = vi.mocked(listProjectOpenQualityIssues);

const FINDING_REQUEST = buildSuggestMatchesRequestFromFindingRow({
  location: "דירה 3",
  trade: "אינסטלציה",
  group_key: "bath",
});

function cachedIssue(id: string): QualityIssue {
  return {
    id,
    organization_id: ORG_ID,
    project_id: PROJECT_ID,
    title: "נזילה",
    severity: "HIGH",
    status: "OPEN",
    location: "דירה 3",
    trade: "אינסטלציה",
    group_key: "bath",
    first_seen_report_id: "report-1",
    first_seen_at: "2026-06-01T10:00:00Z",
    last_seen_report_id: "report-1",
    last_seen_at: "2026-06-01T10:00:00Z",
    recurrence_count: 0,
    photo_ids: [],
    created_at: "2026-06-01T10:00:00Z",
    updated_at: "2026-06-01T10:00:00Z",
  };
}

const API_RESPONSE: QualityIssueSuggestMatchesResponse = {
  project_id: PROJECT_ID,
  match_key: "דירה 3|אינסטלציה|bath",
  total: 1,
  candidates: [
    {
      issue: cachedIssue("issue-api"),
      match_key: "דירה 3|אינסטלציה|bath",
      score: 1,
    },
  ],
};

async function seedOpenIssuesCache(issueId: string) {
  const expiresAt = new Date(Date.now() + 60_000).toISOString();
  mockedListOpen.mockResolvedValue({
    project_id: PROJECT_ID,
    total: 1,
    items: [cachedIssue(issueId)],
  });

  await refreshOpenIssuesCacheForOrganization({
    organizationId: ORG_ID,
    projectIds: [PROJECT_ID],
    expiresAt,
  });
  mockedListOpen.mockClear();
}

describe("resolveProjectQualityIssueMatches (2.1.8)", () => {
  beforeEach(async () => {
    mockedSuggestApi.mockReset();
    mockedListOpen.mockReset();
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
  });

  it("uses API when online and request succeeds", async () => {
    mockedSuggestApi.mockResolvedValue(API_RESPONSE);

    const result = await resolveProjectQualityIssueMatches({
      projectId: PROJECT_ID,
      organizationId: ORG_ID,
      request: FINDING_REQUEST,
      isOnline: true,
    });

    expect(result.candidates[0]?.issue.id).toBe("issue-api");
    expect(mockedSuggestApi).toHaveBeenCalledWith(PROJECT_ID, FINDING_REQUEST);
  });

  it("falls back to IndexedDB cache when offline", async () => {
    await seedOpenIssuesCache("issue-cache");

    const result = await resolveProjectQualityIssueMatches({
      projectId: PROJECT_ID,
      organizationId: ORG_ID,
      request: FINDING_REQUEST,
      isOnline: false,
    });

    expect(result.candidates[0]?.issue.id).toBe("issue-cache");
    expect(mockedSuggestApi).not.toHaveBeenCalled();
  });

  it("falls back to cache when online API fails", async () => {
    await seedOpenIssuesCache("issue-fallback");
    mockedSuggestApi.mockRejectedValueOnce(new Error("network error"));

    const result = await resolveProjectQualityIssueMatches({
      projectId: PROJECT_ID,
      organizationId: ORG_ID,
      request: FINDING_REQUEST,
      isOnline: true,
    });

    expect(result.candidates[0]?.issue.id).toBe("issue-fallback");
    expect(mockedSuggestApi).toHaveBeenCalledTimes(1);
  });

  it("throws when offline without cache", async () => {
    await expect(
      resolveProjectQualityIssueMatches({
        projectId: PROJECT_ID,
        organizationId: ORG_ID,
        request: FINDING_REQUEST,
        isOnline: false,
      })
    ).rejects.toThrow("לא ניתן לטעון ליקויים דומים");
  });
});
