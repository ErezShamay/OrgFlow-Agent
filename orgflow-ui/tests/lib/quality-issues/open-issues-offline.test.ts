import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { clearOfflinePrepBundle } from "@/lib/field-reports/offline-store";
import { saveFromOfflinePrep } from "@/lib/field-reports/repositories/catalog-repository";
import {
  getProjectOpenIssuesFromCache,
  hydrateOpenIssuesCache,
  patchOpenIssuesCacheAfterIssueUpdate,
  refreshOpenIssuesCacheForOrganization,
  suggestProjectQualityIssueMatchesFromCache,
} from "@/lib/quality-issues/open-issues-offline";
import type { QualityIssueOpenListResponse } from "@/lib/quality-issues/types";

vi.mock("@/lib/quality-issues/api", () => ({
  listProjectOpenQualityIssues: vi.fn(),
}));

import { listProjectOpenQualityIssues } from "@/lib/quality-issues/api";

const ORG_ID = "org-open-issues-offline";
const PROJECT_A = "proj-a";
const PROJECT_B = "proj-b";

const mockedListOpen = vi.mocked(listProjectOpenQualityIssues);

function createLocalStorageMock() {
  const store = new Map<string, string>();

  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => {
      store.clear();
    },
  };
}

function openIssuesResponse(
  projectId: string,
  items: QualityIssueOpenListResponse["items"]
): QualityIssueOpenListResponse {
  return {
    project_id: projectId,
    total: items.length,
    items,
  };
}

describe("open-issues-offline (2.1.7)", () => {
  beforeEach(async () => {
    vi.stubGlobal("localStorage", createLocalStorageMock());
    mockedListOpen.mockReset();
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
  });

  it("refreshOpenIssuesCacheForOrganization fetches per project and persists", async () => {
    mockedListOpen.mockImplementation(async (projectId) => {
      if (projectId === PROJECT_A) {
        return openIssuesResponse(PROJECT_A, [
          {
            id: "issue-a",
            organization_id: ORG_ID,
            project_id: PROJECT_A,
            title: "ליקוי A",
            severity: "HIGH",
            status: "OPEN",
            location: "קומה 1",
            trade: "חשמל",
            group_key: "panel",
            first_seen_report_id: "report-a",
            first_seen_at: "2026-06-01T10:00:00Z",
            last_seen_report_id: "report-a",
            last_seen_at: "2026-06-01T10:00:00Z",
            recurrence_count: 0,
            photo_ids: [],
            created_at: "2026-06-01T10:00:00Z",
            updated_at: "2026-06-01T10:00:00Z",
          },
        ]);
      }

      return openIssuesResponse(PROJECT_B, []);
    });

    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
    const saved = await refreshOpenIssuesCacheForOrganization({
      organizationId: ORG_ID,
      projectIds: [PROJECT_A, PROJECT_B, PROJECT_A],
      expiresAt,
    });

    expect(mockedListOpen).toHaveBeenCalledTimes(2);
    expect(saved.projects[PROJECT_A]?.total).toBe(1);
    expect(saved.projects[PROJECT_B]?.total).toBe(0);
    expect(saved.expires_at).toBe(expiresAt);

    await closeFieldReportDatabase();
    const fromCache = await getProjectOpenIssuesFromCache(ORG_ID, PROJECT_A);
    expect(fromCache?.items[0]?.id).toBe("issue-a");
  });

  it("suggestProjectQualityIssueMatchesFromCache ranks cached open issues", async () => {
    const expiresAt = new Date(Date.now() + 60_000).toISOString();
    mockedListOpen.mockResolvedValueOnce(
      openIssuesResponse(PROJECT_A, [
        {
          id: "issue-match",
          organization_id: ORG_ID,
          project_id: PROJECT_A,
          title: "נזילה",
          severity: "CRITICAL",
          status: "OPEN",
          location: "דירה 3",
          trade: "אינסטלציה",
          group_key: "bath",
          catalog_issue_id: "PLB-001",
          first_seen_report_id: "report-1",
          first_seen_at: "2026-06-01T10:00:00Z",
          last_seen_report_id: "report-1",
          last_seen_at: "2026-06-01T10:00:00Z",
          recurrence_count: 0,
          photo_ids: [],
          created_at: "2026-06-01T10:00:00Z",
          updated_at: "2026-06-01T10:00:00Z",
        },
        {
          id: "issue-other",
          organization_id: ORG_ID,
          project_id: PROJECT_A,
          title: "סדק",
          severity: "LOW",
          status: "OPEN",
          location: "דירה 4",
          trade: "טיח",
          group_key: "wall",
          first_seen_report_id: "report-2",
          first_seen_at: "2026-06-02T10:00:00Z",
          last_seen_report_id: "report-2",
          last_seen_at: "2026-06-02T10:00:00Z",
          recurrence_count: 0,
          photo_ids: [],
          created_at: "2026-06-02T10:00:00Z",
          updated_at: "2026-06-02T10:00:00Z",
        },
      ])
    );

    await refreshOpenIssuesCacheForOrganization({
      organizationId: ORG_ID,
      projectIds: [PROJECT_A],
      expiresAt,
    });
    mockedListOpen.mockClear();

    const suggestions = await suggestProjectQualityIssueMatchesFromCache(
      ORG_ID,
      PROJECT_A,
      {
        location: "דירה 3",
        trade: "אינסטלציה",
        group_key: "bath",
        catalog_issue_id: "PLB-001",
      }
    );

    expect(suggestions?.candidates).toHaveLength(1);
    expect(suggestions?.candidates[0]?.issue.id).toBe("issue-match");
    expect(mockedListOpen).not.toHaveBeenCalled();
  });

  it("hydrateOpenIssuesCache loads memory cache for sync reads", async () => {
    const expiresAt = new Date(Date.now() + 60_000).toISOString();
    mockedListOpen.mockResolvedValue(openIssuesResponse(PROJECT_A, []));

    await refreshOpenIssuesCacheForOrganization({
      organizationId: ORG_ID,
      projectIds: [PROJECT_A],
      expiresAt,
    });

    await hydrateOpenIssuesCache(ORG_ID);
    const fromCache = await getProjectOpenIssuesFromCache(ORG_ID, PROJECT_A);
    expect(fromCache?.project_id).toBe(PROJECT_A);
  });

  it("patchOpenIssuesCacheAfterIssueUpdate removes closed and upserts reopened", async () => {
    const expiresAt = new Date(Date.now() + 60_000).toISOString();
    mockedListOpen.mockResolvedValue(
      openIssuesResponse(PROJECT_A, [
        {
          id: "issue-a",
          organization_id: ORG_ID,
          project_id: PROJECT_A,
          title: "ליקוי A",
          severity: "HIGH",
          status: "OPEN",
          first_seen_report_id: "report-a",
          first_seen_at: "2026-06-01T10:00:00Z",
          last_seen_report_id: "report-a",
          last_seen_at: "2026-06-01T10:00:00Z",
          recurrence_count: 0,
          photo_ids: [],
          materialization_key: "report-a:line-a",
        },
      ])
    );

    await refreshOpenIssuesCacheForOrganization({
      organizationId: ORG_ID,
      projectIds: [PROJECT_A],
      expiresAt,
    });

    await patchOpenIssuesCacheAfterIssueUpdate({
      organizationId: ORG_ID,
      projectId: PROJECT_A,
      issue: {
        id: "issue-a",
        organization_id: ORG_ID,
        project_id: PROJECT_A,
        title: "ליקוי A",
        severity: "HIGH",
        status: "CLOSED",
        first_seen_report_id: "report-a",
        first_seen_at: "2026-06-01T10:00:00Z",
        last_seen_report_id: "report-b",
        last_seen_at: "2026-06-09T10:00:00Z",
        recurrence_count: 0,
        photo_ids: [],
        materialization_key: "report-a:line-a",
      },
    });

    let fromCache = await getProjectOpenIssuesFromCache(ORG_ID, PROJECT_A);
    expect(fromCache?.total).toBe(0);

    await patchOpenIssuesCacheAfterIssueUpdate({
      organizationId: ORG_ID,
      projectId: PROJECT_A,
      issue: {
        id: "issue-a",
        organization_id: ORG_ID,
        project_id: PROJECT_A,
        title: "ליקוי A",
        severity: "HIGH",
        status: "REOPENED",
        first_seen_report_id: "report-a",
        first_seen_at: "2026-06-01T10:00:00Z",
        last_seen_report_id: "report-c",
        last_seen_at: "2026-06-09T12:00:00Z",
        recurrence_count: 1,
        photo_ids: [],
        materialization_key: "report-a:line-a",
      },
    });

    fromCache = await getProjectOpenIssuesFromCache(ORG_ID, PROJECT_A);
    expect(fromCache?.total).toBe(1);
    expect(fromCache?.items[0]?.status).toBe("REOPENED");
  });

  it("clearOfflinePrepBundle also clears open issues cache", async () => {
    const expiresAt = new Date(Date.now() + 60_000).toISOString();
    mockedListOpen.mockResolvedValue(openIssuesResponse(PROJECT_A, []));

    await saveFromOfflinePrep(ORG_ID, {
      offline_max_days: 7,
      catalog: {},
      visit_types: [],
      organization_profile: {},
      projects: [{ id: PROJECT_A }],
      reports: [],
    });
    await refreshOpenIssuesCacheForOrganization({
      organizationId: ORG_ID,
      projectIds: [PROJECT_A],
      expiresAt,
    });

    await clearOfflinePrepBundle(ORG_ID);
    expect(await getProjectOpenIssuesFromCache(ORG_ID, PROJECT_A)).toBeNull();
  });
});
