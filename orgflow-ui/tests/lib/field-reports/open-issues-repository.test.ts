import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
  getFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { FIELD_REPORT_STORES } from "@/lib/field-reports/db/schema";
import {
  clearOpenIssuesCacheRecord,
  getProjectOpenIssuesSnapshot,
  isOpenIssuesCacheExpired,
  loadOpenIssuesCacheRecord,
  saveOpenIssuesCacheRecord,
} from "@/lib/field-reports/repositories/open-issues-repository";
import type { QualityIssue } from "@/lib/quality-issues/types";

const ORG_ID = "org-open-issues-cache";
const PROJECT_ID = "proj-1";

function sampleIssue(overrides: Partial<QualityIssue> = {}): QualityIssue {
  return {
    id: "issue-1",
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
    ...overrides,
  };
}

describe("open-issues-repository (2.1.7)", () => {
  beforeEach(async () => {
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
  });

  it("persists open issues cache in IndexedDB open_issues store", async () => {
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
    const saved = await saveOpenIssuesCacheRecord({
      organization_id: ORG_ID,
      cached_at: new Date().toISOString(),
      expires_at: expiresAt,
      projects: {
        [PROJECT_ID]: {
          project_id: PROJECT_ID,
          total: 1,
          items: [sampleIssue()],
        },
      },
    });

    const database = await getFieldReportDatabase();
    const fromStore = await database.get(FIELD_REPORT_STORES.open_issues, ORG_ID);

    expect(fromStore?.organization_id).toBe(ORG_ID);
    expect(fromStore?.projects[PROJECT_ID]?.total).toBe(1);
    expect(isOpenIssuesCacheExpired(saved)).toBe(false);

    await closeFieldReportDatabase();
    const reloaded = await loadOpenIssuesCacheRecord(ORG_ID);
    expect(reloaded?.expires_at).toBe(expiresAt);
  });

  it("returns project snapshot only when cache is valid", async () => {
    const future = new Date(Date.now() + 60_000).toISOString();
    await saveOpenIssuesCacheRecord({
      organization_id: ORG_ID,
      cached_at: new Date().toISOString(),
      expires_at: future,
      projects: {
        [PROJECT_ID]: {
          project_id: PROJECT_ID,
          total: 1,
          items: [sampleIssue({ id: "issue-open" })],
        },
      },
    });

    const snapshot = await getProjectOpenIssuesSnapshot(ORG_ID, PROJECT_ID);
    expect(snapshot?.items[0]?.id).toBe("issue-open");

    await saveOpenIssuesCacheRecord({
      organization_id: ORG_ID,
      cached_at: new Date().toISOString(),
      expires_at: new Date(Date.now() - 1_000).toISOString(),
      projects: {
        [PROJECT_ID]: {
          project_id: PROJECT_ID,
          total: 1,
          items: [sampleIssue({ id: "issue-expired" })],
        },
      },
    });

    expect(await getProjectOpenIssuesSnapshot(ORG_ID, PROJECT_ID)).toBeNull();
  });

  it("clears cache record for organization", async () => {
    await saveOpenIssuesCacheRecord({
      organization_id: ORG_ID,
      cached_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 60_000).toISOString(),
      projects: {},
    });

    await clearOpenIssuesCacheRecord(ORG_ID);
    expect(await loadOpenIssuesCacheRecord(ORG_ID)).toBeNull();
  });
});
