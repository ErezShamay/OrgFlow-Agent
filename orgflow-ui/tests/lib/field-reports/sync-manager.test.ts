import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { saveLinePhotoLocally } from "@/lib/field-reports/line-photo-store";
import {
  enqueueSyncQueueRecord,
  getSyncQueueRecord,
} from "@/lib/field-reports/repositories/sync-queue-repository";
import {
  getLocalReport,
  saveLocalReport,
} from "@/lib/field-reports/repositories/reports-repository";
import {
  clearAllPendingSendRequests,
  loadPendingSendRequests,
} from "@/lib/field-reports/send-queue";
import { buildVisitReportSyncBody } from "@/lib/field-reports/sync/build-sync-body";
import { matchFinalizeApi } from "../../helpers/mock-finalize-api";
import { stubBrowserStorage } from "../../helpers/browser-storage-mock";
import {
  listFieldReportSyncErrorLog,
  resetFieldReportSyncErrorMonitorForTests,
} from "@/lib/field-reports/sync/sync-error-monitor";

const ORG_ID = "org-sync-manager";
const CLIENT_UUID = "a1111111-1111-4111-8111-111111111111";
const CLIENT_LINE = "b2222222-2222-4222-8222-222222222222";
const SERVER_ID = "server-sync-99";

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

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

vi.mock("@/lib/field-reports/report-metadata-draft", () => ({
  flushReportMetadataDraft: vi.fn(async () => undefined),
}));

vi.mock("@/lib/field-reports/pdf/visit-report-pdf-store", () => ({
  hasVisitReportPdfLocally: vi.fn(async () => true),
  loadVisitReportPdfLocally: vi.fn(async () => ({
    reportId: CLIENT_UUID,
    blob: new Blob(["pdf-content"], { type: "application/pdf" }),
    filename: "report.pdf",
    generatedAt: new Date().toISOString(),
  })),
  deleteVisitReportPdfLocally: vi.fn(async () => undefined),
}));

async function seedClosedLocalReport() {
  return saveLocalReport({
    client_report_uuid: CLIENT_UUID,
    organization_id: ORG_ID,
    project_id: "project-1",
    visit_type: "STRUCTURE_SITE",
    visit_date: "2026-06-03",
    header_fields: { contractor_notes: ["שטח"] },
    lines: [
      {
        client_line_uuid: CLIENT_LINE,
        sort_order: 1,
        description: "ממצא",
      },
    ],
    local_status: "LOCAL_CLOSED",
    sync_status: "pending",
    closed_at: "2026-06-03T12:00:00.000Z",
  });
}

describe("SyncManager (FR-025)", () => {
  beforeEach(async () => {
    stubBrowserStorage();
    resetFieldReportSyncErrorMonitorForTests();
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    resetFieldReportSyncErrorMonitorForTests();
    await clearAllPendingSendRequests(ORG_ID);
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("builds sync body from local report", async () => {
    const record = await seedClosedLocalReport();
    const body = buildVisitReportSyncBody(record);

    expect(body.client_report_uuid).toBe(CLIENT_UUID);
    expect(body.lines).toHaveLength(1);
    expect(body.lines[0].client_line_uuid).toBe(CLIENT_LINE);
  });

  it("runs full offline pipeline: upsert, photos, close, finalize", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    await seedClosedLocalReport();
    await enqueueSyncQueueRecord({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
      idempotency_key: `field-report-sync:${CLIENT_UUID}:test`,
    });
    await saveLinePhotoLocally(CLIENT_UUID, CLIENT_LINE, new Blob(["img"]), {
      pendingUpload: true,
      photoId: "photo-1",
    });

    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      const finalize = matchFinalizeApi(path, init, { reportId: SERVER_ID });
      if (finalize) {
        return finalize;
      }

      if (path === "/field-reports/visits/sync" && init?.method === "PUT") {
        return {
          ok: true,
          json: async () => ({
            id: SERVER_ID,
            report: {
              id: SERVER_ID,
              status: "IN_PROGRESS",
              lines: [
                {
                  id: "line-server-1",
                  client_line_uuid: CLIENT_LINE,
                },
              ],
            },
          }),
        } as Response;
      }

      if (
        path.includes("/sync/")
        && path.endsWith("/photos")
        && init?.method === "POST"
      ) {
        return {
          ok: true,
          json: async () => ({
            id: "line-server-1",
            client_line_uuid: CLIENT_LINE,
          }),
        } as Response;
      }

      if (
        path === `/field-reports/visits/${SERVER_ID}`
        && (!init?.method || init.method === "GET")
      ) {
        return {
          ok: true,
          json: async () => ({ id: SERVER_ID, status: "IN_PROGRESS" }),
        } as Response;
      }

      if (path.endsWith("/close") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ id: SERVER_ID, status: "CLOSED" }),
        } as Response;
      }

      return { ok: true, json: async () => ({}) } as Response;
    });

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );

    const result = await SyncManager.runForOrganization(ORG_ID);
    expect(result.processed).toHaveLength(1);
    expect(result.processed[0].success).toBe(true);
    expect(result.processed[0].reportId).toBe(SERVER_ID);

    const local = await getLocalReport(CLIENT_UUID);
    expect(local).toBeNull();
    expect(await loadPendingSendRequests(ORG_ID)).toHaveLength(0);
    expect(await getSyncQueueRecord(CLIENT_UUID)).toBeNull();

    expect(apiFetch).toHaveBeenCalledWith(
      "/field-reports/visits/sync",
      expect.objectContaining({
        method: "PUT",
        headers: {
          "X-Idempotency-Key": CLIENT_UUID,
        },
      })
    );

    const syncPhotoCall = vi.mocked(apiFetch).mock.calls.find(
      (call) =>
        typeof call[0] === "string"
        && call[0].includes("/sync/")
        && call[0].endsWith("/photos")
    );
    expect(syncPhotoCall?.[0]).toBe(
      `/field-reports/visits/sync/${CLIENT_UUID}/lines/${CLIENT_LINE}/photos`
    );
    expect(
      (syncPhotoCall?.[1]?.headers as Record<string, string>)?.[
        "X-Idempotency-Key"
      ]
    ).toBe(CLIENT_LINE);
  });

  it("keeps queue entry on failure with same idempotency key for retry", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    await seedClosedLocalReport();
    const record = await enqueueSyncQueueRecord({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
    });
    const firstKey = record.idempotency_key;

    let finalizeCalls = 0;
    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      if (path === "/field-reports/visits/sync" && init?.method === "PUT") {
        return {
          ok: true,
          json: async () => ({
            id: SERVER_ID,
            report: { id: SERVER_ID, lines: [] },
          }),
        } as Response;
      }

      if (path === `/field-reports/visits/${SERVER_ID}`) {
        return {
          ok: true,
          json: async () => ({ id: SERVER_ID, status: "IN_PROGRESS" }),
        } as Response;
      }

      if (path.endsWith("/close") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ id: SERVER_ID, status: "CLOSED" }),
        } as Response;
      }

      if (path.endsWith("/finalize") && init?.method === "POST") {
        finalizeCalls += 1;
        if (finalizeCalls === 1) {
          return {
            ok: false,
            json: async () => ({
              error: {
                message: "שליחה לליבה נכשלה",
                details: { error_code: "TRANSIENT" },
              },
            }),
          } as Response;
        }
      }

      const finalize = matchFinalizeApi(path, init, { reportId: SERVER_ID });
      if (finalize) {
        return finalize;
      }

      return { ok: true, json: async () => ({}) } as Response;
    });

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );

    const first = await SyncManager.runForOrganization(ORG_ID);
    expect(first.processed[0].success).toBe(false);
    expect(listFieldReportSyncErrorLog()).toHaveLength(1);
    expect(listFieldReportSyncErrorLog()[0].clientReportUuid).toBe(CLIENT_UUID);

    const afterFail = await getSyncQueueRecord(CLIENT_UUID);
    expect(afterFail?.idempotency_key).toBe(firstKey);
    expect(afterFail?.sync_phase).toBe("finalize");

    const second = await SyncManager.runForOrganization(ORG_ID);
    expect(second.processed[0].success).toBe(true);
    expect(await loadPendingSendRequests(ORG_ID)).toHaveLength(0);
    expect(listFieldReportSyncErrorLog()).toHaveLength(0);
  });

  it("delegates server-only queue entries to process-send-queue", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      const finalize = matchFinalizeApi(path, init, { reportId: "report-a" });
      if (finalize) {
        return finalize;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    const { enqueuePendingSendRequest } = await import(
      "@/lib/field-reports/send-queue"
    );
    await enqueuePendingSendRequest(ORG_ID, "report-a");

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );
    const result = await SyncManager.runForOrganization(ORG_ID);

    expect(result.processed[0].success).toBe(true);
    expect(result.processed[0].reportId).toBe("report-a");
    expect(await loadPendingSendRequests(ORG_ID)).toHaveLength(0);
  });

  it("skips close when server report is not IN_PROGRESS", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    await seedClosedLocalReport();
    await enqueueSyncQueueRecord({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
    });

    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      const finalize = matchFinalizeApi(path, init, { reportId: SERVER_ID });
      if (finalize) {
        return finalize;
      }

      if (path === "/field-reports/visits/sync" && init?.method === "PUT") {
        return {
          ok: true,
          json: async () => ({
            id: SERVER_ID,
            report: { id: SERVER_ID, lines: [] },
          }),
        } as Response;
      }

      if (path === `/field-reports/visits/${SERVER_ID}`) {
        return {
          ok: true,
          json: async () => ({ id: SERVER_ID, status: "CLOSED" }),
        } as Response;
      }

      if (path.endsWith("/close") && init?.method === "POST") {
        throw new Error("close should not be called");
      }

      return { ok: true, json: async () => ({}) } as Response;
    });

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );
    const result = await SyncManager.runForOrganization(ORG_ID);

    expect(result.processed[0].success).toBe(true);
    const closeCalls = vi.mocked(apiFetch).mock.calls.filter(
      (call) =>
        typeof call[0] === "string" && call[0].endsWith("/close")
    );
    expect(closeCalls).toHaveLength(0);
  });

  it("stops after upsert+photos for LOCAL_IN_PROGRESS without removing queue", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
      project_id: "project-1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
      lines: [],
      local_status: "LOCAL_IN_PROGRESS",
    });
    await enqueueSyncQueueRecord({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
    });

    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      if (path === "/field-reports/visits/sync" && init?.method === "PUT") {
        return {
          ok: true,
          json: async () => ({
            id: SERVER_ID,
            report: { id: SERVER_ID, lines: [] },
          }),
        } as Response;
      }
      if (path.endsWith("/finalize")) {
        throw new Error("finalize should not run");
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );
    const result = await SyncManager.runForOrganization(ORG_ID);

    expect(result.processed[0].success).toBe(true);
    expect(await loadPendingSendRequests(ORG_ID)).toHaveLength(1);
    const stored = await getSyncQueueRecord(CLIENT_UUID);
    expect(stored?.sync_phase).toBe("photos");
  });
});
