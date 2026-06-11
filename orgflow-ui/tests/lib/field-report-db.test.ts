import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
  getFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { FIELD_REPORT_STORES } from "@/lib/field-reports/db/schema";
import { isClientUuid } from "@/lib/field-reports/ids";
import {
  listLinePhotosForLine,
  saveLinePhotoLocally,
} from "@/lib/field-reports/line-photo-store";
import { resetLinePhotoMigrationMarkerForTests } from "@/lib/field-reports/migrate-line-photos-to-blobs";
import {
  deleteAllBlobsForReport,
  getReportPdfBlob,
  listLinePhotoBlobsForLine,
  saveReportPdfBlob,
} from "@/lib/field-reports/repositories/blobs-repository";
import {
  loadCatalogBundle,
  saveFromOfflinePrep,
} from "@/lib/field-reports/repositories/catalog-repository";
import {
  deleteLocalReport,
  getLocalReport,
  saveLocalReport,
  upsertLine,
} from "@/lib/field-reports/repositories/reports-repository";

const ORG_ID = "org-field-report-db";
const REPORT_UUID = "a1111111-1111-4111-8111-111111111111";
const LINE_ONE = "b2222222-2222-4222-8222-222222222222";
const LINE_TWO = "c3333333-3333-4333-8333-333333333333";

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

/** סוגר חיבור - הקריאה הבאה ל-repository פותחת מחדש (כמו רענון אפליקציה). */
async function simulateAppRestart() {
  await closeFieldReportDatabase();
}

describe("field-report IndexedDB round-trip (FR-008)", () => {
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
  });

  it("persists catalog, report, lines, photos, and PDF across reconnect", async () => {
    await saveFromOfflinePrep(ORG_ID, {
      offline_max_days: 7,
      catalog_version: "catalog-v1",
      catalog: { families: [{ top_family: "SAFETY" }] },
      visit_types: [{ code: "safety_visit", label_he: "בטיחות" }],
      organization_profile: { name: "OrgFlow" },
      projects: [{ id: "project-1", name: "פרויקט א" }],
      reports: [],
    });

    await saveLocalReport({
      client_report_uuid: REPORT_UUID,
      organization_id: ORG_ID,
      project_id: "project-1",
      visit_type: "safety_visit",
      visit_date: "2026-06-03",
      header_fields: { contractor_notes: "הערות" },
      local_status: "LOCAL_IN_PROGRESS",
      lines: [
        {
          client_line_uuid: LINE_ONE,
          id: LINE_ONE,
          sort_order: 1,
          description: "ממצא א",
          has_photo: true,
        },
      ],
    });

    await upsertLine(REPORT_UUID, {
      client_line_uuid: LINE_TWO,
      id: LINE_TWO,
      sort_order: 2,
      description: "ממצא ב",
    });

    await saveLinePhotoLocally(REPORT_UUID, LINE_ONE, new Blob(["photo-a"]), {
      pendingUpload: true,
      photoId: "photo-a",
    });
    await saveLinePhotoLocally(REPORT_UUID, LINE_ONE, new Blob(["photo-b"]), {
      pendingUpload: false,
      photoId: "photo-b",
    });
    await saveLinePhotoLocally(REPORT_UUID, LINE_TWO, new Blob(["photo-c"]), {
      pendingUpload: true,
      photoId: "photo-c",
    });

    await saveReportPdfBlob(
      REPORT_UUID,
      new Blob(["%PDF-1.4"], { type: "application/pdf" }),
      "visit-report.pdf"
    );

    await simulateAppRestart();

    const catalog = await loadCatalogBundle(ORG_ID);
    expect(catalog?.catalog_version).toBe("catalog-v1");
    expect(catalog?.projects).toHaveLength(1);

    const report = await getLocalReport(REPORT_UUID);
    expect(report?.lines).toHaveLength(2);
    expect(report?.header_fields).toEqual({ contractor_notes: "הערות" });
    expect(isClientUuid(report?.client_report_uuid)).toBe(true);
    expect(isClientUuid(report?.lines[0].client_line_uuid)).toBe(true);

    const lineOnePhotos = await listLinePhotosForLine(REPORT_UUID, LINE_ONE);
    expect(lineOnePhotos.map((photo) => photo.photoId).sort()).toEqual([
      "photo-a",
      "photo-b",
    ]);
    expect(lineOnePhotos.find((photo) => photo.photoId === "photo-a")?.pendingUpload).toBe(
      true
    );

    const lineTwoPhotos = await listLinePhotoBlobsForLine(REPORT_UUID, LINE_TWO);
    expect(lineTwoPhotos).toHaveLength(1);
    expect(lineTwoPhotos[0].photo_id).toBe("photo-c");

    const pdf = await getReportPdfBlob(REPORT_UUID);
    expect(pdf?.filename).toBe("visit-report.pdf");
    expect(await pdf?.blob.text()).toBe("%PDF-1.4");
  });

  it("exposes all field-report stores on the unified database", async () => {
    const database = await getFieldReportDatabase();

    expect(database.objectStoreNames.contains(FIELD_REPORT_STORES.catalog)).toBe(
      true
    );
    expect(database.objectStoreNames.contains(FIELD_REPORT_STORES.reports)).toBe(
      true
    );
    expect(database.objectStoreNames.contains(FIELD_REPORT_STORES.blobs)).toBe(
      true
    );
    expect(database.objectStoreNames.contains(FIELD_REPORT_STORES.sync_queue)).toBe(
      true
    );
  });

  it("deleteLocalReport keeps blobs until deleteAllBlobsForReport", async () => {
    await saveLocalReport({
      client_report_uuid: REPORT_UUID,
      organization_id: ORG_ID,
      project_id: "project-1",
      visit_type: "safety_visit",
      visit_date: "2026-06-03",
      header_fields: {},
      lines: [
        {
          client_line_uuid: LINE_ONE,
          id: LINE_ONE,
          sort_order: 1,
        },
      ],
    });

    await saveLinePhotoLocally(REPORT_UUID, LINE_ONE, new Blob(["x"]), {
      pendingUpload: true,
    });
    await saveReportPdfBlob(REPORT_UUID, new Blob(["pdf"]), "r.pdf");

    await deleteLocalReport(REPORT_UUID);
    expect(await getLocalReport(REPORT_UUID)).toBeNull();
    expect(await listLinePhotosForLine(REPORT_UUID, LINE_ONE)).toHaveLength(1);
    expect(await getReportPdfBlob(REPORT_UUID)).not.toBeNull();

    await deleteAllBlobsForReport(REPORT_UUID);
    expect(await listLinePhotosForLine(REPORT_UUID, LINE_ONE)).toHaveLength(0);
    expect(await getReportPdfBlob(REPORT_UUID)).toBeNull();
  });
});
