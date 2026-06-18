import "fake-indexeddb/auto";

import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  finishLocalVisitReportWithPdf,
} from "@/lib/field-reports/close-local-visit-report";
import { resolveFieldReportDataSource } from "@/lib/field-reports/data-source";
import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { isClientUuid } from "@/lib/field-reports/ids";
import {
  listLinePhotosForLine,
  listPendingLinePhotos,
  saveLinePhotoLocally,
} from "@/lib/field-reports/line-photo-store";
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
import { probeFieldReportNetworkStatus } from "@/lib/field-reports/sync/network-status";
import {
  loadVisitReportForPage,
  localVisitReportToView,
} from "@/lib/field-reports/visit-report-view";

import config from "../../../capacitor.config";

const UI_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../.."
);

const ORG_ID = "org-phase-d-gate";
const USER_ID = "user-phase-d-gate";
const SERVER_ID = "server-phase-d-gate";

const {
  getNetworkStatus,
  addNetworkListener,
  writeFile,
  readFile,
  getUri,
  rmdir,
  takePhoto,
  chooseFromGallery,
} = vi.hoisted(() => ({
  getNetworkStatus: vi.fn(),
  addNetworkListener: vi.fn(),
  writeFile: vi.fn(),
  readFile: vi.fn(),
  getUri: vi.fn(),
  rmdir: vi.fn(),
  takePhoto: vi.fn(),
  chooseFromGallery: vi.fn(),
}));

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => true),
    getPlatform: vi.fn(() => "android"),
    convertFileSrc: vi.fn((uri: string) => `converted:${uri}`),
  },
}));

vi.mock("@capacitor/network", () => ({
  Network: {
    getStatus: getNetworkStatus,
    addListener: addNetworkListener,
  },
}));

vi.mock("@capacitor/filesystem", () => ({
  Directory: { Data: "DATA" },
  Encoding: { UTF8: "utf8" },
  Filesystem: {
    writeFile,
    readFile,
    getUri,
    rmdir,
  },
}));

vi.mock("@capacitor/camera", () => ({
  Camera: {
    takePhoto,
    chooseFromGallery,
  },
  CameraDirection: { Rear: "REAR" },
}));

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

vi.mock("@/lib/field-reports/pdf/generate-visit-report-pdf", () => ({
  generateVisitReportPdf: vi.fn(async () =>
    new Blob(["pdf-gate-d-bytes"], { type: "application/pdf" })
  ),
}));

vi.mock("@/lib/field-reports/report-metadata-draft", () => ({
  flushReportMetadataDraft: vi.fn(async () => undefined),
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

async function resetNativeCapacitorMocks(connected: boolean) {
  const { resetCapacitorFieldReportNetworkForTests } = await import(
    "@/lib/capacitor/field-report-network"
  );
  resetCapacitorFieldReportNetworkForTests();

  getNetworkStatus.mockResolvedValue({ connected });
  addNetworkListener.mockResolvedValue({ remove: vi.fn() });
  writeFile.mockResolvedValue({ uri: "file:///data/report.pdf" });
  getUri.mockResolvedValue({ uri: "file:///data/report.pdf" });

  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(new Blob(["x"], { type: "image/jpeg" }), {
      status: 200,
    }))
  );
}

async function runOfflinePrepBundle() {
  return saveFromOfflinePrep(ORG_ID, {
    offline_max_days: 7,
    catalog_version: "gate-d-v1",
    catalog: { families: [{ top_family: "SAFETY" }] },
    visit_types: [
      { code: "safety_visit", label_he: "ביקור בטיחות" },
    ],
    organization_profile: { name: "OrgFlow Gate D" },
    projects: [{ id: "project-gate-d", name: "פרויקט שטח APK" }],
    reports: [],
  });
}

async function createFullNativeOfflineFieldReport(fetchSpy: ReturnType<typeof vi.fn>) {
  await runOfflinePrepBundle();

  const catalog = await loadCatalogBundle(ORG_ID);
  expect(catalog?.projects).toHaveLength(1);

  const localReport = await createLocalVisitReport({
    organizationId: ORG_ID,
    userId: USER_ID,
    projectId: "project-gate-d",
    projectName: "פרויקט שטח APK",
    visitType: "safety_visit",
    visitTypeLabelHe: "ביקור בטיחות",
    visitDate: "2026-06-04",
    catalogVersion: catalog?.catalog_version ?? null,
    organizationProfileSnapshot: catalog?.organization_profile ?? null,
  });

  const clientReportUuid = localReport.client_report_uuid;
  expect(isClientUuid(clientReportUuid)).toBe(true);

  await saveLocalReport({
    ...localReport,
    header_fields: {
      ...localReport.header_fields,
      contractor_notes: ["כותרת שטח - Gate ד"],
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
    lineUuids.push(updated!.lines[index].client_line_uuid);
  }

  const { takeLinePhotoWithNativeCamera, isNativeLinePhotoPicker } =
    await import("@/lib/capacitor/line-photo-picker");

  expect(isNativeLinePhotoPicker()).toBe(true);

  takePhoto.mockResolvedValue({
    webPath: "capacitor://localhost/cam.jpg",
    metadata: { format: "jpeg" },
  });

  for (const lineUuid of lineUuids.slice(0, 3)) {
    const file = await takeLinePhotoWithNativeCamera();
    expect(file).toBeInstanceOf(File);
    await saveLinePhotoLocally(clientReportUuid, lineUuid, file!, {
      pendingUpload: true,
      photoId: `native-${lineUuid.slice(0, 8)}`,
    });
  }

  const beforeClose = (await getLocalReport(clientReportUuid))!;
  const dataSource = resolveFieldReportDataSource(
    { navigatorOnline: false, apiReachable: false },
    { hasLocalReport: true, serverReportId: null }
  );
  expect(dataSource.mode).toBe("local-only");
  expect(dataSource.canCallVisitReportApi).toBe(false);

  const view = localVisitReportToView(beforeClose);
  const finishResult = await finishLocalVisitReportWithPdf({
    report: view,
    inspector: { full_name: "מפקח Gate D" },
  });

  expect(finishResult.record.local_status).toBe("LOCAL_CLOSED");
  expect(finishResult.pdfSource).toBe("generated");
  expect(await hasReportPdfBlob(clientReportUuid)).toBe(true);
  expect(writeFile).toHaveBeenCalled();
  expect(
    fetchSpy.mock.calls.every(([url]) => String(url).startsWith("capacitor://"))
  ).toBe(true);

  return { clientReportUuid, lineUuids };
}

/**
 * קריטריוני Gate שלב ד (§8 בתוכנית, FR-035).
 * APK / Capacitor native - prep, עריכה, PDF, מצלמה, סנכרון תמונות.
 */
describe("phase D gate acceptance (FR-035)", () => {
  beforeEach(async () => {
    vi.stubGlobal("localStorage", createLocalStorageMock());
    resetLinePhotoMigrationMarkerForTests();
    await deleteFieldReportDatabase();
    await resetNativeCapacitorMocks(false);
  });

  afterEach(async () => {
    resetLinePhotoMigrationMarkerForTests();
    const { resetCapacitorFieldReportNetworkForTests } = await import(
      "@/lib/capacitor/field-report-network"
    );
    resetCapacitorFieldReportNetworkForTests();
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("§8.1 - APK targets Android 10+ (minSdk 29) with ElayoAI package and build scripts", () => {
    const variablesGradle = readFileSync(
      path.join(UI_ROOT, "android/variables.gradle"),
      "utf8"
    );
    expect(variablesGradle).toMatch(/minSdkVersion\s*=\s*29/);

    const appGradle = readFileSync(
      path.join(UI_ROOT, "android/app/build.gradle"),
      "utf8"
    );
    expect(appGradle).toContain('applicationId "com.elayoai.app"');

    expect(config.appId).toBe("com.elayoai.app");
    expect(config.webDir).toBe("out");

    const pkg = JSON.parse(
      readFileSync(path.join(UI_ROOT, "package.json"), "utf8")
    ) as { scripts?: Record<string, string> };
    expect(pkg.scripts?.["cap:apk:debug"]).toBeTruthy();
    expect(pkg.scripts?.["cap:apk:release"]).toBeTruthy();
    expect(existsSync(path.join(UI_ROOT, "scripts/build-android-apk.mjs"))).toBe(
      true
    );

    const manifest = readFileSync(
      path.join(UI_ROOT, "android/app/src/main/AndroidManifest.xml"),
      "utf8"
    );
    expect(manifest).toContain("android.permission.INTERNET");
  });

  it("§8.2 - airplane mode on native: prep, 5 lines, 3 native photos, close, PDF, no API", async () => {
    const fetchSpy = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.startsWith("capacitor://")) {
        return new Response(new Blob(["photo-bytes"], { type: "image/jpeg" }), {
          status: 200,
        });
      }
      throw new Error(`unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchSpy);

    const pingRequest = vi.fn();
    const offlineSnapshot = await probeFieldReportNetworkStatus({
      request: pingRequest,
    });
    expect(offlineSnapshot).toEqual({
      navigatorOnline: false,
      apiReachable: false,
    });
    expect(pingRequest).not.toHaveBeenCalled();

    const { clientReportUuid, lineUuids } =
      await createFullNativeOfflineFieldReport(fetchSpy);

    const closed = await getLocalReport(clientReportUuid);
    expect(closed?.local_status).toBe("LOCAL_CLOSED");
    expect(closed?.lines).toHaveLength(5);
    expect(await countSyncQueueForUser(ORG_ID, USER_ID)).toBe(1);

    expect(
      (await listLinePhotosForLine(clientReportUuid, lineUuids[0])).length
    ).toBe(1);
    expect(await listLinePhotoBlobsForLine(clientReportUuid, lineUuids[0])).toHaveLength(1);
    expect(await hasReportPdfBlob(clientReportUuid)).toBe(true);
    expect(writeFile.mock.calls.some((call) =>
      String(call[0]?.path).includes("field-reports/pdfs")
    )).toBe(true);

    await closeFieldReportDatabase();

    const reloaded = await getLocalReport(clientReportUuid);
    expect(reloaded?.local_status).toBe("LOCAL_CLOSED");

    const pageLoad = await loadVisitReportForPage(clientReportUuid, {
      navigatorOnline: false,
      apiReachable: false,
    });
    expect(pageLoad.source).toBe("local");
    expect(pageLoad.dataSource.mode).toBe("local-only");
    expect(
      fetchSpy.mock.calls.every(([url]) => String(url).startsWith("capacitor://"))
    ).toBe(true);
  });

  it("§8.3 - native camera photos sync to core after network returns", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    const fetchSpy = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.startsWith("capacitor://")) {
        return new Response(new Blob(["photo-bytes"], { type: "image/jpeg" }), {
          status: 200,
        });
      }
      throw new Error(`unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchSpy);

    const { clientReportUuid, lineUuids } =
      await createFullNativeOfflineFieldReport(fetchSpy);

    const pendingBefore = await listPendingLinePhotos(clientReportUuid);
    expect(pendingBefore.length).toBeGreaterThanOrEqual(3);

    await resetNativeCapacitorMocks(true);

    const photoUploadPaths: string[] = [];

    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
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
        photoUploadPaths.push(path);
        return {
          ok: true,
          json: async () => ({
            id: `server-line-${photoUploadPaths.length}`,
            client_line_uuid: lineUuids[photoUploadPaths.length - 1],
          }),
        } as Response;
      }

      if (path.endsWith("/request-send") && init?.method === "POST") {
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
    const result = await SyncManager.runForOrganization(ORG_ID);

    expect(result.processed).toHaveLength(1);
    expect(result.processed[0].success).toBe(true);
    expect(photoUploadPaths.length).toBeGreaterThanOrEqual(3);
    expect(
      photoUploadPaths.every((uploadPath) =>
        uploadPath.includes(`/sync/${clientReportUuid}/lines/`)
      )
    ).toBe(true);

    const pendingAfter = await listPendingLinePhotos(clientReportUuid);
    expect(pendingAfter).toHaveLength(0);

    const local = await getLocalReport(clientReportUuid);
    expect(local).toBeNull();
  });
});
