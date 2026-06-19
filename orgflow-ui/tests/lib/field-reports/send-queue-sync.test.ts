import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { getSyncQueueRecord } from "@/lib/field-reports/repositories/sync-queue-repository";
import {
  clearAllPendingSendRequests,
  enqueuePendingSendRequest,
  loadPendingSendRequests,
  pendingSendPhaseLabelHe,
  removePendingSendRequest,
  syncQueueRecordToPendingSendRequest,
  updatePendingSendRequest,
} from "@/lib/field-reports/send-queue";
import { LEGACY_ORGFLOW_FIELD_REPORTS_SEND_QUEUE_PREFIX } from "@/lib/elayoai/keys";
import { saveLocalReport } from "@/lib/field-reports/repositories/reports-repository";

const ORG_ID = "org-send-queue-sync";
const CLIENT_UUID = "a1111111-1111-4111-8111-111111111111";
const SERVER_ID = "server-report-42";

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

function seedLegacySendQueue(
  organizationId: string,
  entries: Array<{
    reportId: string;
    idempotencyKey?: string;
    syncPhase?: string;
  }>
) {
  localStorage.setItem(
    `${LEGACY_ORGFLOW_FIELD_REPORTS_SEND_QUEUE_PREFIX}:${organizationId}`,
    JSON.stringify(
      entries.map((entry) => ({
        reportId: entry.reportId,
        organizationId,
        requestedAt: "2026-06-03T10:00:00.000Z",
        idempotencyKey:
          entry.idempotencyKey || `legacy:${entry.reportId}`,
        syncPhase: entry.syncPhase,
      }))
    )
  );
}

describe("send-queue IndexedDB bridge (FR-024)", () => {
  beforeEach(async () => {
    const localStorageMock = createLocalStorageMock();
    vi.stubGlobal("localStorage", localStorageMock);
    vi.stubGlobal("window", { localStorage: localStorageMock });
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
  });

  it("enqueues and removes pending send requests per organization", async () => {
    await enqueuePendingSendRequest("org-1", "report-a");
    await enqueuePendingSendRequest("org-1", "report-b");

    expect(await loadPendingSendRequests("org-1")).toHaveLength(2);

    await removePendingSendRequest("org-1", "report-a");
    const remaining = await loadPendingSendRequests("org-1");
    expect(remaining).toHaveLength(1);
    expect(remaining[0].reportId).toBe("report-b");
  });

  it("replaces an existing queue entry for the same report", async () => {
    const first = await enqueuePendingSendRequest("org-1", "report-a");
    await updatePendingSendRequest("org-1", "report-a", {
      syncPhase: "photos",
      lastError: "retry",
    });
    const second = await enqueuePendingSendRequest("org-1", "report-a");

    expect(second.syncPhase).toBe("queued");
    expect(second.lastError).toBeUndefined();
    expect(second.idempotencyKey).toBe(first.idempotencyKey);
  });

  it("maps sync phases to Hebrew labels", () => {
    expect(pendingSendPhaseLabelHe("photos")).toContain("תמונות");
    expect(pendingSendPhaseLabelHe("request_send")).toContain("מעבד דוח");
  });

  it("migrates legacy localStorage queue into IndexedDB once", async () => {
    seedLegacySendQueue(ORG_ID, [
      {
        reportId: SERVER_ID,
        idempotencyKey: "legacy-idem-1",
        syncPhase: "photos",
      },
    ]);

    await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      server_report_id: SERVER_ID,
      organization_id: ORG_ID,
      project_id: "p1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
    });

    const pending = await loadPendingSendRequests(ORG_ID);
    expect(pending).toHaveLength(1);
    expect(pending[0].clientReportUuid).toBe(CLIENT_UUID);
    expect(pending[0].reportId).toBe(SERVER_ID);
    expect(pending[0].idempotencyKey).toBe("legacy-idem-1");
    expect(pending[0].syncPhase).toBe("photos");

    expect(
      localStorage.getItem(`elayoai-field-reports-send-queue:${ORG_ID}`)
    ).toBeNull();

    const secondLoad = await loadPendingSendRequests(ORG_ID);
    expect(secondLoad).toHaveLength(1);

    const stored = await getSyncQueueRecord(CLIENT_UUID);
    expect(stored?.client_report_uuid).toBe(CLIENT_UUID);
  });

  it("resolves client_report_uuid when enqueueing by server id", async () => {
    await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      server_report_id: SERVER_ID,
      organization_id: ORG_ID,
      project_id: "p1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
    });

    const pending = await enqueuePendingSendRequest(ORG_ID, SERVER_ID);
    expect(pending.clientReportUuid).toBe(CLIENT_UUID);
    expect(pending.reportId).toBe(SERVER_ID);

    const stored = await getSyncQueueRecord(CLIENT_UUID);
    expect(stored?.server_report_id).toBe(SERVER_ID);
  });

  it("clears all pending sends for an organization", async () => {
    await enqueuePendingSendRequest("org-1", "report-a");
    await enqueuePendingSendRequest("org-1", "report-b");
    await enqueuePendingSendRequest("org-2", "report-c");

    await clearAllPendingSendRequests("org-1");

    expect(await loadPendingSendRequests("org-1")).toHaveLength(0);
    expect(await loadPendingSendRequests("org-2")).toHaveLength(1);
  });

  it("maps sync queue records to pending send requests", async () => {
    const record = await enqueuePendingSendRequest(ORG_ID, CLIENT_UUID);
    const stored = await getSyncQueueRecord(CLIENT_UUID);
    expect(stored).not.toBeNull();
    expect(syncQueueRecordToPendingSendRequest(stored!)).toEqual(record);
  });
});
