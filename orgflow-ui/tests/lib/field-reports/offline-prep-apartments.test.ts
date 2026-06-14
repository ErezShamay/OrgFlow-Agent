import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { listApartmentsFromOfflineBundle } from "@/lib/field-reports/offline-prep-apartments";
import type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";
import { saveOfflinePrepBundle } from "@/lib/field-reports/offline-store";
import { parseSupervisionCatalogFromBundle } from "@/lib/field-reports/supervision-catalog";
import {
  createSupervisionLocalReport,
} from "@/lib/field-reports/supervision-new-report";
import type { SupervisionCatalog } from "@/lib/field-reports/schema/types";

const ORG_ID = "org-offline-f";

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

const sampleSupervisionCatalog: SupervisionCatalog = {
  catalog_version: "1.4.0-supervision-checklist",
  issues: [
    {
      issue_id: "SUP-FIN-004",
      issue_name_he: "פוגות",
      standard_ref: 'ת"י 1555',
      top_family: "FINISHING_WORKS",
      category_id: "TILING",
      category_name_he: "ריצוף",
      scope: "APARTMENT",
      allowed_stages: ["FINISHING"],
    },
  ],
};

function buildOfflineBundle(): Omit<
  OfflinePrepBundle,
  "prepared_at" | "expires_at"
> {
  return {
    organization_id: ORG_ID,
    offline_max_days: 7,
    catalog_version: "1.4.0-supervision-checklist",
    catalog: { issues: [] },
    supervision_catalog: sampleSupervisionCatalog,
    public_areas: [{ id: "LOBBY", label_he: "לובי / כניסה" }],
    apartments_by_project: {
      "proj-offline": [
        {
          id: "apt-7",
          organization_id: ORG_ID,
          project_id: "proj-offline",
          apartment_number: "7",
          group_key: "apartment:7",
          owner_name: "ישראל ישראלי",
          invite_status: "none",
        },
      ],
    },
    visit_types: [],
    organization_profile: {},
    projects: [{ id: "proj-offline" }],
    reports: [],
  };
}

describe("listApartmentsFromOfflineBundle (§12.1)", () => {
  it("returns apartments for project from offline prep bundle", () => {
    const apartments = listApartmentsFromOfflineBundle(
      buildOfflineBundle() as OfflinePrepBundle,
      "proj-offline"
    );

    expect(apartments).toHaveLength(1);
    expect(apartments[0]?.apartment_number).toBe("7");
    expect(apartments[0]?.owner_name).toBe("ישראל ישראלי");
  });

  it("returns empty list when project is missing from bundle", () => {
    expect(
      listApartmentsFromOfflineBundle(
        buildOfflineBundle() as OfflinePrepBundle,
        "missing-project"
      )
    ).toEqual([]);
  });
});

describe("offline supervision report creation (§12.4 gate)", () => {
  beforeEach(async () => {
    vi.stubGlobal("localStorage", createLocalStorageMock());
    vi.stubGlobal("fetch", vi.fn());
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
  });

  it("creates local supervision report from offline prep without network", async () => {
    const saved = await saveOfflinePrepBundle(ORG_ID, buildOfflineBundle());
    const catalog = parseSupervisionCatalogFromBundle(saved);

    expect(catalog?.issues).toHaveLength(1);

    const apartments = listApartmentsFromOfflineBundle(saved, "proj-offline");
    expect(apartments[0]?.id).toBe("apt-7");

    const report = await createSupervisionLocalReport({
      organizationId: ORG_ID,
      projectId: "proj-offline",
      visitDate: "2026-06-14",
      catalog: catalog!,
      constructionStage: "FINISHING",
      visitScope: "APARTMENT",
      apartmentId: apartments[0]?.id ?? null,
      apartmentNumber: apartments[0]?.apartment_number ?? null,
      ownerName: apartments[0]?.owner_name ?? null,
      catalogVersion: saved.catalog_version ?? null,
    });

    expect(report.visit_type).toBe("FINISHING_APARTMENTS");
    expect(report.header_fields?.supervision_meta).toMatchObject({
      apartment_number: "7",
      owner_name: "ישראל ישראלי",
    });
    expect(vi.mocked(fetch)).not.toHaveBeenCalled();
  });
});
