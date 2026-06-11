import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { closeLocalVisitReport } from "@/lib/field-reports/close-local-visit-report";
import { isClientUuid } from "@/lib/field-reports/ids";
import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { createLocalVisitReport } from "@/lib/field-reports/new-report-form";
import { resetLinePhotoMigrationMarkerForTests } from "@/lib/field-reports/migrate-line-photos-to-blobs";
import {
  saveFromOfflinePrep,
} from "@/lib/field-reports/repositories/catalog-repository";
import { getSyncQueueRecord } from "@/lib/field-reports/repositories/sync-queue-repository";
import {
  getLocalReport,
  upsertLine,
} from "@/lib/field-reports/repositories/reports-repository";
import {
  clearAllPendingSendRequests,
  loadPendingSendRequests,
} from "@/lib/field-reports/send-queue";
import {
  enrichSyncPanelQueueEntries,
} from "@/lib/field-reports/sync-panel-queue";
import {
  buildSyncProgressLabel,
  queueEntriesWithErrors,
  shouldShowSyncPanel,
} from "@/lib/field-reports/sync-panel-view";
import { buildVisitReportSyncBody } from "@/lib/field-reports/sync/build-sync-body";
import type { SyncManagerProgressEvent } from "@/lib/field-reports/sync/sync-manager";

const ORG_ID = "org-phase-c-gate";
const USER_ID = "user-phase-c-gate";
const PROJECT_GATE_C = "project-gate-c-core";
const SERVER_ID = "server-phase-c-gate";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

vi.mock("@/lib/field-reports/report-metadata-draft", () => ({
  flushReportMetadataDraft: vi.fn(async () => undefined),
}));

vi.mock("@/lib/field-reports/pdf/visit-report-pdf-store", () => ({
  hasVisitReportPdfLocally: vi.fn(async () => true),
  loadVisitReportPdfLocally: vi.fn(async () => ({
    reportId: "pdf-report",
    blob: new Blob(["pdf-gate-c"], { type: "application/pdf" }),
    filename: "report.pdf",
    generatedAt: new Date().toISOString(),
  })),
  deleteVisitReportPdfLocally: vi.fn(async () => undefined),
}));

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

function parseSyncPutBody(init?: RequestInit): Record<string, unknown> {
  const raw = init?.body;
  if (typeof raw !== "string") {
    throw new Error("expected JSON sync body");
  }

  return JSON.parse(raw) as Record<string, unknown>;
}

async function runOfflinePrep() {
  await saveFromOfflinePrep(ORG_ID, {
    offline_max_days: 7,
    catalog_version: "gate-c-v1",
    catalog: { families: [{ top_family: "SAFETY" }] },
    visit_types: [
      { code: "safety_visit", label_he: "ביקור בטיחות" },
    ],
    organization_profile: { name: "OrgFlow Gate C" },
    projects: [{ id: PROJECT_GATE_C, name: "פרויקט ליבה" }],
    reports: [],
  });
}

/** דוח שטח סגור - prep → יצירה → שורה → סגירה → תור. */
async function createFieldReportReadyForSync() {
  await runOfflinePrep();

  const localReport = await createLocalVisitReport({
    organizationId: ORG_ID,
    userId: USER_ID,
    projectId: PROJECT_GATE_C,
    projectName: "פרויקט ליבה",
    visitType: "safety_visit",
    visitTypeLabelHe: "ביקור בטיחות",
    visitDate: "2026-06-03",
    catalogVersion: "gate-c-v1",
    organizationProfileSnapshot: { name: "OrgFlow Gate C" },
  });

  const clientReportUuid = localReport.client_report_uuid;
  expect(isClientUuid(clientReportUuid)).toBe(true);

  await upsertLine(clientReportUuid, {
    sort_order: 1,
    description: "ממצא Gate ג",
    has_photo: false,
  });

  await closeLocalVisitReport(clientReportUuid);

  const closed = await getLocalReport(clientReportUuid);
  expect(closed?.local_status).toBe("LOCAL_CLOSED");
  expect(closed?.project_id).toBe(PROJECT_GATE_C);
  expect(buildVisitReportSyncBody(closed!).project_id).toBe(PROJECT_GATE_C);

  return { clientReportUuid, closed: closed! };
}

async function mockSuccessfulSyncPipeline(clientReportUuid: string) {
  const { apiFetch } = await import("@/lib/api/client");
  vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
    if (path === "/field-reports/visits/sync" && init?.method === "PUT") {
      return {
        ok: true,
        json: async () => ({
          id: SERVER_ID,
          report: {
            id: SERVER_ID,
            status: "IN_PROGRESS",
            lines: [],
          },
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

    if (path.endsWith("/request-send") && init?.method === "POST") {
      const key = (init?.headers as Record<string, string>)?.[
        "X-Idempotency-Key"
      ];
      expect(key).toBeTruthy();
      return {
        ok: true,
        json: async () => ({ id: SERVER_ID, status: "LOCKED" }),
      } as Response;
    }

    if (
      typeof path === "string"
      && path.includes(clientReportUuid)
      && path.endsWith("/photos")
    ) {
      return {
        ok: true,
        json: async () => ({}),
      } as Response;
    }

    return { ok: true, json: async () => ({}) } as Response;
  });
}

/**
 * קריטריוני Gate שלב ג (§7 בתוכנית, FR-028).
 * זרימת שטח → SyncManager (mock API) + UI sync panel (לוגיקת תצוגה).
 */
describe("phase C gate acceptance (FR-028)", () => {
  beforeEach(async () => {
    vi.stubGlobal("localStorage", createLocalStorageMock());
    vi.stubGlobal("window", { localStorage: createLocalStorageMock() });
    resetLinePhotoMigrationMarkerForTests();
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    resetLinePhotoMigrationMarkerForTests();
    await clearAllPendingSendRequests(ORG_ID);
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("§7.1 - field report created on device syncs with correct project_id to core", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    const { clientReportUuid } = await createFieldReportReadyForSync();

    await mockSuccessfulSyncPipeline(clientReportUuid);

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );
    const result = await SyncManager.runForOrganization(ORG_ID);

    expect(result.processed).toHaveLength(1);
    expect(result.processed[0].success).toBe(true);
    expect(result.processed[0].reportId).toBe(SERVER_ID);

    const syncCall = vi.mocked(apiFetch).mock.calls.find(
      (call) =>
        call[0] === "/field-reports/visits/sync"
        && call[1]?.method === "PUT"
    );
    expect(syncCall).toBeDefined();

    const body = parseSyncPutBody(syncCall![1]);
    expect(body.project_id).toBe(PROJECT_GATE_C);
    expect(body.client_report_uuid).toBe(clientReportUuid);
    expect(syncCall![1]?.headers).toMatchObject({
      "X-Idempotency-Key": clientReportUuid,
    });

    const requestSendCall = vi.mocked(apiFetch).mock.calls.find(
      (call) =>
        typeof call[0] === "string"
        && call[0].endsWith("/request-send")
    );
    expect(requestSendCall?.[0]).toBe(
      `/field-reports/visits/${SERVER_ID}/request-send`
    );

    const local = await getLocalReport(clientReportUuid);
    expect(local).toBeNull();
    expect(await loadPendingSendRequests(ORG_ID)).toHaveLength(0);
  });

  it("§7.2 - retry after disconnect: same idempotency, single request-send, no duplicate queue", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    const { clientReportUuid } = await createFieldReportReadyForSync();

    const queueBefore = await getSyncQueueRecord(clientReportUuid);
    expect(queueBefore?.idempotency_key).toBeTruthy();
    const idempotencyKey = queueBefore!.idempotency_key;

    let syncPutCount = 0;
    let requestSendCount = 0;

    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      if (path === "/field-reports/visits/sync" && init?.method === "PUT") {
        syncPutCount += 1;
        expect(init?.headers).toMatchObject({
          "X-Idempotency-Key": clientReportUuid,
        });
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

      if (path.endsWith("/request-send") && init?.method === "POST") {
        requestSendCount += 1;
        if (requestSendCount === 1) {
          return {
            ok: false,
            json: async () => ({
              error: { message: "ניתוק רשת - שליחה נכשלה" },
            }),
          } as Response;
        }
        return {
          ok: true,
          json: async () => ({ id: SERVER_ID, status: "LOCKED" }),
        } as Response;
      }

      return { ok: true, json: async () => ({}) } as Response;
    });

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );

    const first = await SyncManager.runForOrganization(ORG_ID);
    expect(first.processed[0].success).toBe(false);
    expect(requestSendCount).toBe(1);
    expect(syncPutCount).toBe(1);

    const afterFail = await getSyncQueueRecord(clientReportUuid);
    expect(afterFail?.idempotency_key).toBe(idempotencyKey);
    expect(afterFail?.last_error).toBeTruthy();

    const second = await SyncManager.runForOrganization(ORG_ID);
    expect(second.processed[0].success).toBe(true);
    expect(requestSendCount).toBe(2);
    expect(syncPutCount).toBe(2);
    expect(await loadPendingSendRequests(ORG_ID)).toHaveLength(0);

    const third = await SyncManager.runForOrganization(ORG_ID);
    expect(third.processed).toHaveLength(0);
    expect(requestSendCount).toBe(2);
  });

  it("§7.3 - sync progress phases and per-report errors for SyncPanel", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    const { clientReportUuid } = await createFieldReportReadyForSync();

    const progressEvents: SyncManagerProgressEvent[] = [];

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

      if (path.endsWith("/request-send") && init?.method === "POST") {
        return {
          ok: false,
          json: async () => ({
            error: { message: "שגיאת ליבה - Gate ג" },
          }),
        } as Response;
      }

      return { ok: true, json: async () => ({}) } as Response;
    });

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );

    await SyncManager.runForOrganization(ORG_ID, undefined, {
      onProgress: (event) => {
        progressEvents.push(event);
      },
    });

    expect(progressEvents.length).toBeGreaterThan(0);
    expect(progressEvents.some((event) => event.phase === "upsert")).toBe(true);
    expect(progressEvents.some((event) => event.phase === "request_send")).toBe(
      true
    );

    const active = progressEvents[progressEvents.length - 1];
    const progressLabel = buildSyncProgressLabel(
      active.index,
      active.total,
      active.phase
    );
    expect(progressLabel).toMatch(/דוח \d+ מתוך \d+/);

    const pending = await loadPendingSendRequests(ORG_ID);
    const enriched = await enrichSyncPanelQueueEntries(pending);
    const withErrors = queueEntriesWithErrors(enriched);

    expect(withErrors).toHaveLength(1);
    expect(withErrors[0].lastError).toContain("שגיאת ליבה");
    expect(withErrors[0].displayLabel).toContain("פרויקט");

    expect(
      shouldShowSyncPanel({
        pendingCount: pending.length,
        syncing: false,
        hasQueueErrors: withErrors.length > 0,
        lastRunSummary: null,
      })
    ).toBe(true);
  });
});
