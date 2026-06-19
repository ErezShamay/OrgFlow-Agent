import "fake-indexeddb/auto";

import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { closeLocalVisitReport } from "@/lib/field-reports/close-local-visit-report";
import { resolveFieldReportDataSource } from "@/lib/field-reports/data-source";
import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import {
  assertFieldReportLogoutAllowed,
  getFieldReportLogoutBlock,
} from "@/lib/field-reports/field-report-logout-block";
import { importInProgressReportsFromOfflinePrep } from "@/lib/field-reports/import-in-progress-reports";
import { isClientUuid } from "@/lib/field-reports/ids";
import { MAX_LINE_PHOTOS } from "@/lib/field-reports/line-photo-constants";
import {
  listPendingLinePhotos,
  saveLinePhotoLocally,
} from "@/lib/field-reports/line-photo-store";
import { resetLinePhotoMigrationMarkerForTests } from "@/lib/field-reports/migrate-line-photos-to-blobs";
import { createLocalVisitReport } from "@/lib/field-reports/new-report-form";
import {
  listLinePhotoBlobsForReport,
} from "@/lib/field-reports/repositories/blobs-repository";
import {
  loadCatalogBundle,
  saveFromOfflinePrep,
} from "@/lib/field-reports/repositories/catalog-repository";
import {
  getLocalReport,
  saveLocalReport,
  upsertLine,
} from "@/lib/field-reports/repositories/reports-repository";
import {
  countSyncQueueForUser,
  enqueueSyncQueueRecord,
} from "@/lib/field-reports/repositories/sync-queue-repository";
import { loadPendingSendRequests } from "@/lib/field-reports/send-queue";
import { buildVisitReportSyncBody } from "@/lib/field-reports/sync/build-sync-body";
import {
  FIELD_REPORT_SYNC_ERROR_LOG_KEY,
  listFieldReportSyncErrorLog,
  resetFieldReportSyncErrorMonitorForTests,
} from "@/lib/field-reports/sync/sync-error-monitor";
import { matchFinalizeApi } from "../../helpers/mock-finalize-api";
import { loadVisitReportForPage } from "@/lib/field-reports/visit-report-view";

const REPO_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../../.."
);

const ORG_ID = "org-phase-e-gate";
const USER_A = "user-phase-e-a";
const USER_B = "user-phase-e-b";
const PROJECT_ID = "project-phase-e-core";
const SERVER_ID = "server-phase-e-gate";

const OFFLINE_NETWORK = {
  navigatorOnline: false,
  apiReachable: false,
} as const;

const VOLUME_LINE_COUNT = 6;
const VOLUME_PHOTOS_TOTAL = VOLUME_LINE_COUNT * MAX_LINE_PHOTOS;

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
    blob: new Blob(["pdf-gate-e"], { type: "application/pdf" }),
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

async function runOfficePrep() {
  return saveFromOfflinePrep(ORG_ID, {
    offline_max_days: 7,
    catalog_version: "gate-e-v1",
    catalog: { families: [{ top_family: "SAFETY" }] },
    visit_types: [
      { code: "safety_visit", label_he: "ביקור בטיחות" },
    ],
    organization_profile: { name: "OrgFlow Gate E" },
    projects: [{ id: PROJECT_ID, name: "פרויקט השקה" }],
    reports: [{ id: "server-office-e", status: "IN_PROGRESS" }],
  });
}

async function mockSuccessfulCoreSync(
  clientReportUuid: string,
  lineUuids: string[],
  options?: { trackPhotoUploads?: boolean }
) {
  const { apiFetch } = await import("@/lib/api/client");
  const photoUploadPaths: string[] = [];

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
            lines: lineUuids.map((uuid, index) => ({
              id: `server-line-${index + 1}`,
              client_line_uuid: uuid,
            })),
          },
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

    if (
      typeof path === "string"
      && path.includes("/photos")
      && init?.method === "POST"
    ) {
      if (options?.trackPhotoUploads) {
        photoUploadPaths.push(path);
      }
      return {
        ok: true,
        json: async () => ({
          id: `server-line-${photoUploadPaths.length}`,
          client_line_uuid: lineUuids[0],
        }),
      } as Response;
    }

    return { ok: true, json: async () => ({}) } as Response;
  });

  return { photoUploadPaths };
}

/**
 * קריטריוני Gate שלב ה (§9 בתוכנית, FR-038).
 * השקה - משרד→שטח→סנכרון→ליבה, טאבלט משותף, נפח תמונות, תיעוד וניטור.
 */
describe("phase E gate acceptance (FR-038)", () => {
  beforeEach(async () => {
    vi.stubGlobal("localStorage", createLocalStorageMock());
    resetLinePhotoMigrationMarkerForTests();
    resetFieldReportSyncErrorMonitorForTests();
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    resetLinePhotoMigrationMarkerForTests();
    resetFieldReportSyncErrorMonitorForTests();
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("§9.1 - office prep → field offline → office sync → core (project_id, queue empty)", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    await runOfficePrep();
    expect((await loadCatalogBundle(ORG_ID))?.projects).toHaveLength(1);

    const serverReport = {
      id: "server-office-e",
      status: "IN_PROGRESS",
      project_id: PROJECT_ID,
      project_name: "פרויקט משרד",
      visit_type: "safety_visit",
      visit_type_label_he: "ביקור בטיחות",
      visit_date: "2026-06-04",
      header_fields: { contractor_notes: ["ממשרד"] },
      lines: [
        {
          id: "line-office-e",
          sort_order: 1,
          description: "ממצא מיובא",
          has_photo: false,
        },
      ],
    };

    const importResult = await importInProgressReportsFromOfflinePrep({
      organizationId: ORG_ID,
      userId: USER_A,
      prepReports: [{ id: "server-office-e", status: "IN_PROGRESS" }],
      fetchVisitReport: async (id) =>
        id === "server-office-e" ? serverReport : null,
    });
    expect(importResult.imported).toBe(1);

    const localReport = await createLocalVisitReport({
      organizationId: ORG_ID,
      userId: USER_A,
      projectId: PROJECT_ID,
      projectName: "פרויקט השקה",
      visitType: "safety_visit",
      visitTypeLabelHe: "ביקור בטיחות",
      visitDate: "2026-06-04",
      catalogVersion: "gate-e-v1",
      organizationProfileSnapshot: { name: "OrgFlow Gate E" },
    });

    const clientReportUuid = localReport.client_report_uuid;
    expect(isClientUuid(clientReportUuid)).toBe(true);

    const line = (await upsertLine(clientReportUuid, {
      sort_order: 1,
      description: "ממצא שטח - Gate ה",
      has_photo: true,
    }))!.lines[0];

    await saveLinePhotoLocally(
      clientReportUuid,
      line.client_line_uuid,
      new Blob(["field-photo"], { type: "image/jpeg" }),
      { pendingUpload: true, photoId: "gate-e-photo-1" }
    );

    await closeLocalVisitReport(clientReportUuid);

    const offlineLoad = await loadVisitReportForPage(
      clientReportUuid,
      OFFLINE_NETWORK
    );
    expect(offlineLoad.source).toBe("local");
    expect(offlineLoad.dataSource.mode).toBe("local-only");
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(await countSyncQueueForUser(ORG_ID, USER_A)).toBe(1);

    const closed = (await getLocalReport(clientReportUuid))!;
    expect(buildVisitReportSyncBody(closed).project_id).toBe(PROJECT_ID);

    await mockSuccessfulCoreSync(clientReportUuid, [
      line.client_line_uuid,
    ]);

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );
    const result = await SyncManager.runForOrganization(ORG_ID);

    expect(result.processed).toHaveLength(1);
    expect(result.processed[0].success).toBe(true);

    const { apiFetch } = await import("@/lib/api/client");
    const syncCall = vi.mocked(apiFetch).mock.calls.find(
      (call) =>
        call[0] === "/field-reports/visits/sync"
        && call[1]?.method === "PUT"
    );
    expect(parseSyncPutBody(syncCall![1]).project_id).toBe(PROJECT_ID);

    const synced = await getLocalReport(clientReportUuid);
    expect(synced).toBeNull();
    expect(await loadPendingSendRequests(ORG_ID)).toHaveLength(0);
    expect(listFieldReportSyncErrorLog()).toHaveLength(0);
  });

  it("§9.2 - shared tablet: user A blocked on logout when queue pending; user B allowed", async () => {
    const clientUuid = "c3333333-3333-4333-8333-333333333333";

    await saveLocalReport({
      client_report_uuid: clientUuid,
      organization_id: ORG_ID,
      user_id: USER_A,
      project_id: PROJECT_ID,
      visit_type: "safety_visit",
      visit_date: "2026-06-04",
      header_fields: {},
      local_status: "LOCAL_IN_PROGRESS",
      sync_status: "done",
    });

    await closeLocalVisitReport(clientUuid);

    const blockA = await getFieldReportLogoutBlock(ORG_ID, USER_A);
    expect(blockA?.summary.syncQueueCount).toBe(1);
    await expect(
      assertFieldReportLogoutAllowed(ORG_ID, USER_A)
    ).rejects.toThrow(/לא ניתן להתנתק/);

    await saveLocalReport({
      client_report_uuid: "d4444444-4444-4444-8444-444444444444",
      organization_id: ORG_ID,
      user_id: USER_B,
      project_id: PROJECT_ID,
      visit_type: "safety_visit",
      visit_date: "2026-06-04",
      header_fields: {},
      local_status: "LOCAL_IN_PROGRESS",
      sync_status: "done",
    });

    const blockB = await getFieldReportLogoutBlock(ORG_ID, USER_B);
    expect(blockB).toBeNull();
    await expect(
      assertFieldReportLogoutAllowed(ORG_ID, USER_B)
    ).resolves.toBeUndefined();
  });

  it(`§9.3 - volume: ${VOLUME_PHOTOS_TOTAL} photos (${VOLUME_LINE_COUNT}×${MAX_LINE_PHOTOS}) sync and indexed blob size`, async () => {
    const localReport = await createLocalVisitReport({
      organizationId: ORG_ID,
      userId: USER_A,
      projectId: PROJECT_ID,
      projectName: "פרויקט נפח",
      visitType: "safety_visit",
      visitTypeLabelHe: "ביקור בטיחות",
      visitDate: "2026-06-04",
      catalogVersion: null,
      organizationProfileSnapshot: null,
    });

    const clientReportUuid = localReport.client_report_uuid;
    const lineUuids: string[] = [];
    const photoBytes = 48_000;

    for (let lineIndex = 0; lineIndex < VOLUME_LINE_COUNT; lineIndex += 1) {
      const updated = await upsertLine(clientReportUuid, {
        sort_order: lineIndex + 1,
        description: `שורה נפח ${lineIndex + 1}`,
        has_photo: true,
      });
      const lineUuid = updated!.lines[lineIndex].client_line_uuid;
      lineUuids.push(lineUuid);

      for (let photoIndex = 0; photoIndex < MAX_LINE_PHOTOS; photoIndex += 1) {
        await saveLinePhotoLocally(
          clientReportUuid,
          lineUuid,
          new Blob([`x`.repeat(photoBytes)], { type: "image/jpeg" }),
          {
            pendingUpload: true,
            photoId: `vol-${lineIndex}-${photoIndex}`,
          }
        );
      }
    }

    await closeLocalVisitReport(clientReportUuid);

    const pending = await listPendingLinePhotos(clientReportUuid);
    expect(pending).toHaveLength(VOLUME_PHOTOS_TOTAL);

    const blobs = await listLinePhotoBlobsForReport(clientReportUuid);
    const totalBytes = blobs.reduce((sum, record) => sum + record.blob.size, 0);
    expect(totalBytes).toBe(VOLUME_PHOTOS_TOTAL * photoBytes);

    const { photoUploadPaths } = await mockSuccessfulCoreSync(
      clientReportUuid,
      lineUuids,
      { trackPhotoUploads: true }
    );

    const { SyncManager } = await import(
      "@/lib/field-reports/sync/sync-manager"
    );
    const result = await SyncManager.runForOrganization(ORG_ID);

    expect(result.processed[0].success).toBe(true);
    expect(photoUploadPaths.length).toBe(VOLUME_PHOTOS_TOTAL);
    expect((await listPendingLinePhotos(clientReportUuid))).toHaveLength(0);

    const dataSource = resolveFieldReportDataSource(
      { navigatorOnline: true, apiReachable: true },
      { hasLocalReport: true, serverReportId: SERVER_ID }
    );
    expect(dataSource.mode).toBe("hybrid");
  });

  it("§9.4 - inspector guide and sync docs cover prep, field, finalize, logout", () => {
    const inspectorGuide = path.join(
      REPO_ROOT,
      "docs/field-reports-inspector-guide.md"
    );
    const syncMonitoring = path.join(
      REPO_ROOT,
      "docs/field-reports-sync-monitoring.md"
    );

    expect(existsSync(inspectorGuide)).toBe(true);
    expect(existsSync(syncMonitoring)).toBe(true);

    const guideText = readFileSync(inspectorGuide, "utf8");
    expect(guideText).toContain("הכנה לא מקוון");
    expect(guideText).toContain("בשטח");
    expect(guideText).toContain("Finalize");
    expect(guideText).toContain("לא ניתן להתנתק");
    expect(guideText).toContain("field-reports-sync-monitoring.md");
  });

  it("§9.5 - sync error monitor wired: failure logs, success clears (FR-037)", async () => {
    const clientUuid = "e5555555-5555-4555-8555-555555555555";
    const clientLineUuid = "f6666666-6666-4666-8666-666666666666";

    await saveLocalReport({
      client_report_uuid: clientUuid,
      organization_id: ORG_ID,
      project_id: PROJECT_ID,
      visit_type: "safety_visit",
      visit_date: "2026-06-04",
      header_fields: {},
      lines: [
        {
          client_line_uuid: clientLineUuid,
          sort_order: 1,
          description: "ממצא",
          has_photo: false,
        },
      ],
      local_status: "LOCAL_CLOSED",
      sync_status: "pending",
      closed_at: "2026-06-04T12:00:00.000Z",
    });

    await enqueueSyncQueueRecord({
      client_report_uuid: clientUuid,
      organization_id: ORG_ID,
    });

    const { apiFetch } = await import("@/lib/api/client");
    let finalizeCount = 0;

    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      if (path === "/field-reports/visits/sync" && init?.method === "PUT") {
        return {
          ok: true,
          json: async () => ({
            id: SERVER_ID,
            report: {
              id: SERVER_ID,
              lines: [
                {
                  id: "server-line-1",
                  client_line_uuid: clientLineUuid,
                },
              ],
            },
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
        finalizeCount += 1;
        if (finalizeCount === 1) {
          return {
            ok: false,
            json: async () => ({
              error: { message: "שגיאת ליבה - Gate ה" },
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
    expect(listFieldReportSyncErrorLog()[0].phase).toBeTruthy();

    const monitoringDoc = path.join(
      REPO_ROOT,
      "docs/field-reports-sync-monitoring.md"
    );
    expect(readFileSync(monitoringDoc, "utf8")).toContain(
      FIELD_REPORT_SYNC_ERROR_LOG_KEY
    );

    const second = await SyncManager.runForOrganization(ORG_ID);
    expect(second.processed[0].success).toBe(true);
    expect(listFieldReportSyncErrorLog()).toHaveLength(0);
  });
});
