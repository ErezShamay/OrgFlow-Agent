import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import {
  assertFieldReportLogoutAllowed,
  getFieldReportLogoutBlock,
} from "@/lib/field-reports/field-report-logout-block";
import { closeLocalVisitReport } from "@/lib/field-reports/close-local-visit-report";
import {
  enqueuePendingSendRequest,
  loadPendingSendRequests,
} from "@/lib/field-reports/send-queue";
import { saveLocalReport } from "@/lib/field-reports/repositories/reports-repository";

const ORG_ID = "org-logout-block";
const USER_ID = "user-logout-1";
const CLIENT_UUID = "a1111111-1111-4111-8111-111111111111";

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

describe("field-report-logout-block (FR-018)", () => {
  beforeEach(async () => {
    const localStorageMock = createLocalStorageMock();
    vi.stubGlobal("localStorage", localStorageMock);
    vi.stubGlobal("window", { localStorage: localStorageMock });
    await deleteFieldReportDatabase();
    await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
      user_id: USER_ID,
      project_id: "p1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
      local_status: "LOCAL_IN_PROGRESS",
    });
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
  });

  it("allows logout when no pending field work", async () => {
    await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
      user_id: USER_ID,
      project_id: "p1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
      local_status: "LOCAL_IN_PROGRESS",
      sync_status: "done",
    });

    const block = await getFieldReportLogoutBlock(ORG_ID, USER_ID);
    expect(block).toBeNull();
    await expect(
      assertFieldReportLogoutAllowed(ORG_ID, USER_ID)
    ).resolves.toBeUndefined();
  });

  it("blocks logout after local close enqueues sync_queue", async () => {
    await closeLocalVisitReport(CLIENT_UUID);

    const block = await getFieldReportLogoutBlock(ORG_ID, USER_ID);
    expect(block?.summary.syncQueueCount).toBe(1);
    expect(block?.summary.pendingLocalReportCount).toBe(1);
    expect(block?.summary.pendingReportCount).toBe(1);
    expect(block?.summary.total).toBe(1);
    expect(block?.message).toMatch(/דוח אחד ממתין להעלאה/);
    expect(block?.message).not.toMatch(/·/);
    await expect(
      assertFieldReportLogoutAllowed(ORG_ID, USER_ID)
    ).rejects.toThrow(/לא ניתן להתנתק/);
  });

  it("allows logout for in-progress draft with default pending sync_status", async () => {
    const block = await getFieldReportLogoutBlock(ORG_ID, USER_ID);
    expect(block).toBeNull();
    await expect(
      assertFieldReportLogoutAllowed(ORG_ID, USER_ID)
    ).resolves.toBeUndefined();
  });

  it("blocks logout when pending send queue has entries", async () => {
    await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
      user_id: USER_ID,
      project_id: "p1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
      local_status: "LOCAL_IN_PROGRESS",
      sync_status: "done",
    });
    await enqueuePendingSendRequest(ORG_ID, "server-report-1");
    expect(await loadPendingSendRequests(ORG_ID)).toHaveLength(1);

    const block = await getFieldReportLogoutBlock(ORG_ID, USER_ID);
    expect(block?.summary.syncQueueCount).toBe(1);
    expect(block?.summary.pendingSendCount).toBe(0);
    expect(block?.summary.total).toBe(1);
  });
});
