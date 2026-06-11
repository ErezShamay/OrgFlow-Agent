import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
  getFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { FIELD_REPORT_STORES } from "@/lib/field-reports/db/schema";
import { isClientUuid } from "@/lib/field-reports/ids";
import { resetLinePhotoMigrationMarkerForTests } from "@/lib/field-reports/migrate-line-photos-to-blobs";
import {
  isExpired,
  loadCatalogBundle,
  saveFromOfflinePrep,
} from "@/lib/field-reports/repositories/catalog-repository";
import {
  getLocalReport,
  saveLocalReport,
} from "@/lib/field-reports/repositories/reports-repository";

const ORG_ID = "org-phase-a-gate";

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

/**
 * קריטריוני Gate שלב א (§5 בתוכנית, FR-009).
 * ממופה לבדיקות אוטומטיות - ללא קריאות רשת.
 */
describe("phase A gate acceptance (FR-009)", () => {
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

  it("§5.1 - offline prep bundle persists in IndexedDB catalog for 7 days", async () => {
    const saved = await saveFromOfflinePrep(ORG_ID, {
      offline_max_days: 7,
      catalog_version: "gate-v1",
      catalog: { families: [{ top_family: "SAFETY" }] },
      visit_types: [],
      organization_profile: {},
      projects: [{ id: "p1" }],
      reports: [],
    });

    const database = await getFieldReportDatabase();
    const fromStore = await database.get(FIELD_REPORT_STORES.catalog, ORG_ID);

    expect(fromStore?.organization_id).toBe(ORG_ID);
    expect(fromStore?.catalog_version).toBe("gate-v1");

    const preparedMs = new Date(saved.prepared_at).getTime();
    const expiresMs = new Date(saved.expires_at).getTime();
    expect(expiresMs - preparedMs).toBe(7 * 24 * 60 * 60 * 1000);
    expect(isExpired(saved)).toBe(false);

    await closeFieldReportDatabase();
    const reloaded = await loadCatalogBundle(ORG_ID);
    expect(reloaded?.expires_at).toBe(saved.expires_at);
  });

  it("§5.2 - local report is created with client UUID without network", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const report = await saveLocalReport({
      organization_id: ORG_ID,
      project_id: "project-gate",
      visit_type: "safety_visit",
      visit_date: "2026-06-03",
      header_fields: { notes: "מקומי" },
      lines: [
        {
          description: "שורה ראשונה",
        },
      ],
    });

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(isClientUuid(report.client_report_uuid)).toBe(true);
    expect(isClientUuid(report.lines[0].client_line_uuid)).toBe(true);
    expect(report.local_status).toBe("LOCAL_DRAFT");
  });

  it("§5.3 - report survives closing and reopening the database connection", async () => {
    const reportUuid = "d4444444-4444-4444-8444-444444444444";

    await saveLocalReport({
      client_report_uuid: reportUuid,
      organization_id: ORG_ID,
      project_id: "project-gate",
      visit_type: "safety_visit",
      visit_date: "2026-06-03",
      header_fields: { contractor_notes: "לפני סגירה" },
      lines: [
        {
          client_line_uuid: "e5555555-5555-4555-8555-555555555555",
          id: "e5555555-5555-4555-8555-555555555555",
          sort_order: 1,
          description: "ממצא",
        },
      ],
    });

    await closeFieldReportDatabase();

    const reloaded = await getLocalReport(reportUuid);
    expect(reloaded?.header_fields).toEqual({ contractor_notes: "לפני סגירה" });
    expect(reloaded?.lines[0].description).toBe("ממצא");
  });
});
