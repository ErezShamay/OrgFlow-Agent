import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  finishLocalVisitReportWithPdf,
} from "@/lib/field-reports/close-local-visit-report";
import { resolveFieldReportDataSource } from "@/lib/field-reports/data-source";
import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { importInProgressReportsFromOfflinePrep } from "@/lib/field-reports/import-in-progress-reports";
import { isClientUuid } from "@/lib/field-reports/ids";
import { listLinePhotosForLine, saveLinePhotoLocally } from "@/lib/field-reports/line-photo-store";
import { resetLinePhotoMigrationMarkerForTests } from "@/lib/field-reports/migrate-line-photos-to-blobs";
import { createLocalVisitReport } from "@/lib/field-reports/new-report-form";
import {
  hasReportPdfBlob,
  listLinePhotoBlobsForLine,
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
} from "@/lib/field-reports/repositories/sync-queue-repository";
import {
  loadVisitReportForPage,
  localVisitReportToView,
} from "@/lib/field-reports/visit-report-view";

const ORG_ID = "org-phase-b-gate";
const USER_ID = "user-phase-b-gate";
const SERVER_REPORT_ID = "server-office-in-progress";

const OFFLINE_NETWORK = {
  navigatorOnline: false,
  apiReachable: false,
} as const;

vi.mock("@/lib/field-reports/pdf/generate-visit-report-pdf", () => ({
  generateVisitReportPdf: vi.fn(async () =>
    new Blob(["pdf-gate-bytes"], { type: "application/pdf" })
  ),
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

/** סימולציית רענון דף / סגירת טאב - סגירת חיבור IndexedDB. */
async function simulatePageRefresh() {
  await closeFieldReportDatabase();
}

async function runOfflinePrepBundle() {
  return saveFromOfflinePrep(ORG_ID, {
    offline_max_days: 7,
    catalog_version: "gate-b-v1",
    catalog: { families: [{ top_family: "SAFETY" }] },
    visit_types: [
      { code: "safety_visit", label_he: "ביקור בטיחות" },
    ],
    organization_profile: { name: "OrgFlow Gate B" },
    projects: [{ id: "project-gate-b", name: "פרויקט שטח" }],
    reports: [{ id: SERVER_REPORT_ID, status: "IN_PROGRESS" }],
  });
}

async function createFullOfflineFieldReport(fetchSpy: ReturnType<typeof vi.fn>) {
  await runOfflinePrepBundle();

  const catalog = await loadCatalogBundle(ORG_ID);
  expect(catalog?.projects).toHaveLength(1);

  const localReport = await createLocalVisitReport({
    organizationId: ORG_ID,
    userId: USER_ID,
    projectId: "project-gate-b",
    projectName: "פרויקט שטח",
    visitType: "safety_visit",
    visitTypeLabelHe: "ביקור בטיחות",
    visitDate: "2026-06-03",
    catalogVersion: catalog?.catalog_version ?? null,
    organizationProfileSnapshot: catalog?.organization_profile ?? null,
  });

  const clientReportUuid = localReport.client_report_uuid;
  expect(isClientUuid(clientReportUuid)).toBe(true);

  await saveLocalReport({
    ...localReport,
    header_fields: {
      ...localReport.header_fields,
      contractor_notes: ["כותרת שטח - Gate ב"],
    },
    local_status: "LOCAL_IN_PROGRESS",
  });

  const lineDescriptions = [
    "שורה 1 - ממצא",
    "שורה 2 - ממצא",
    "שורה 3 - ממצא",
    "שורה 4 - ממצא",
    "שורה 5 - ממצא",
  ];

  const lineUuids: string[] = [];

  for (const [index, description] of lineDescriptions.entries()) {
    const updated = await upsertLine(clientReportUuid, {
      sort_order: index + 1,
      description,
      has_photo: index < 3,
    });
    const line = updated?.lines[index];
    expect(line?.description).toBe(description);
    lineUuids.push(line!.client_line_uuid);
  }

  await saveLinePhotoLocally(
    clientReportUuid,
    lineUuids[0],
    new Blob(["photo-1"], { type: "image/jpeg" }),
    { pendingUpload: true, photoId: "gate-photo-1" }
  );
  await saveLinePhotoLocally(
    clientReportUuid,
    lineUuids[1],
    new Blob(["photo-2"], { type: "image/jpeg" }),
    { pendingUpload: true, photoId: "gate-photo-2" }
  );
  await saveLinePhotoLocally(
    clientReportUuid,
    lineUuids[2],
    new Blob(["photo-3"], { type: "image/jpeg" }),
    { pendingUpload: true, photoId: "gate-photo-3" }
  );

  const beforeClose = (await getLocalReport(clientReportUuid))!;
  expect(beforeClose.lines).toHaveLength(5);
  expect(beforeClose.header_fields.contractor_notes).toEqual([
    "כותרת שטח - Gate ב",
  ]);

  const dataSource = resolveFieldReportDataSource(OFFLINE_NETWORK, {
    hasLocalReport: true,
    serverReportId: null,
  });
  expect(dataSource.mode).toBe("local-only");
  expect(dataSource.canCallVisitReportApi).toBe(false);

  const view = localVisitReportToView(beforeClose);
  const finishResult = await finishLocalVisitReportWithPdf({
    report: view,
    inspector: { full_name: "מפקח Gate B" },
  });

  expect(finishResult.record.local_status).toBe("LOCAL_CLOSED");
  expect(finishResult.pdfSource).toBe("generated");
  expect(await hasReportPdfBlob(clientReportUuid)).toBe(true);
  expect(fetchSpy).not.toHaveBeenCalled();

  return {
    clientReportUuid,
    lineUuids,
  };
}

/**
 * קריטריוני Gate שלב ב (§6 בתוכנית, FR-019).
 * סימולציה ללא רשת - prep, עריכה, סגירה, רענון, ייבוא משרד.
 */
describe("phase B gate acceptance (FR-019)", () => {
  beforeEach(async () => {
    vi.stubGlobal("localStorage", createLocalStorageMock());
    resetLinePhotoMigrationMarkerForTests();
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    resetLinePhotoMigrationMarkerForTests();
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("§6.1 - airplane mode: header, 5 lines, 3 photos, close, PDF without API", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const { clientReportUuid, lineUuids } =
      await createFullOfflineFieldReport(fetchSpy);

    const closed = await getLocalReport(clientReportUuid);
    expect(closed?.local_status).toBe("LOCAL_CLOSED");
    expect(closed?.lines).toHaveLength(5);
    expect(closed?.closed_at).toBeTruthy();
    expect(await countSyncQueueForUser(ORG_ID, USER_ID)).toBe(1);

    const photosLine0 = await listLinePhotosForLine(
      clientReportUuid,
      lineUuids[0]
    );
    const photosLine1 = await listLinePhotosForLine(
      clientReportUuid,
      lineUuids[1]
    );
    const photosLine2 = await listLinePhotosForLine(
      clientReportUuid,
      lineUuids[2]
    );
    expect(photosLine0).toHaveLength(1);
    expect(photosLine1).toHaveLength(1);
    expect(photosLine2).toHaveLength(1);

    const blobsLine0 = await listLinePhotoBlobsForLine(
      clientReportUuid,
      lineUuids[0]
    );
    expect(blobsLine0).toHaveLength(1);
    expect(await hasReportPdfBlob(clientReportUuid)).toBe(true);
  });

  it("§6.2 - page refresh: report, lines, photos, and PDF persist in IndexedDB", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const { clientReportUuid, lineUuids } =
      await createFullOfflineFieldReport(fetchSpy);

    await simulatePageRefresh();

    const reloaded = await getLocalReport(clientReportUuid);
    expect(reloaded?.local_status).toBe("LOCAL_CLOSED");
    expect(reloaded?.lines).toHaveLength(5);
    expect(reloaded?.header_fields.contractor_notes).toEqual([
      "כותרת שטח - Gate ב",
    ]);
    expect(reloaded?.lines[4].description).toBe("שורה 5 - ממצא");

    expect(
      (await listLinePhotosForLine(clientReportUuid, lineUuids[0])).map(
        (photo) => photo.photoId
      )
    ).toEqual(["gate-photo-1"]);
    expect(await hasReportPdfBlob(clientReportUuid)).toBe(true);

    const pageLoad = await loadVisitReportForPage(
      clientReportUuid,
      OFFLINE_NETWORK
    );
    expect(pageLoad.source).toBe("local");
    expect(pageLoad.dataSource.mode).toBe("local-only");
    expect(pageLoad.report.lines).toHaveLength(5);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("§6.3 - office IN_PROGRESS report imported at prep, opens offline without API", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    await runOfflinePrepBundle();

    const serverReport = {
      id: SERVER_REPORT_ID,
      status: "IN_PROGRESS",
      project_id: "project-gate-b",
      project_name: "פרויקט משרד",
      visit_type: "safety_visit",
      visit_type_label_he: "ביקור בטיחות",
      visit_date: "2026-06-03",
      header_fields: { contractor_notes: ["מהמשרד"] },
      lines: [
        {
          id: "line-office-1",
          sort_order: 1,
          description: "ממצא ממשרד - Gate ב",
          has_photo: false,
        },
      ],
    };

    const importResult = await importInProgressReportsFromOfflinePrep({
      organizationId: ORG_ID,
      userId: USER_ID,
      prepReports: [{ id: SERVER_REPORT_ID, status: "IN_PROGRESS" }],
      fetchVisitReport: async (id) => {
        fetchSpy(id);
        return id === SERVER_REPORT_ID ? serverReport : null;
      },
    });

    expect(importResult.imported).toBe(1);
    expect(importResult.failed).toEqual([]);

    fetchSpy.mockClear();

    await simulatePageRefresh();

    const offlineLoad = await loadVisitReportForPage(
      SERVER_REPORT_ID,
      OFFLINE_NETWORK
    );

    expect(offlineLoad.source).toBe("local");
    expect(offlineLoad.report.project_name).toBe("פרויקט משרד");
    expect(offlineLoad.report.lines[0].description).toBe(
      "ממצא ממשרד - Gate ב"
    );
    expect(offlineLoad.dataSource.canCallVisitReportApi).toBe(false);
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
