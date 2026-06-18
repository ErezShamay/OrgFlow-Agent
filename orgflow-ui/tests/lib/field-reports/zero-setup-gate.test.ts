/**
 * Gate — Zero Setup Z4 (COMPETITIVE-LAYER-TASKS.md).
 * Auto offline prep after project create / workspace entry — no manual step.
 */
import "fake-indexeddb/auto";

import { readFileSync } from "node:fs";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
  getFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { FIELD_REPORT_STORES } from "@/lib/field-reports/db/schema";
import {
  ensureOfflinePrepForProject,
  fetchAndPersistOfflinePrepBundle,
  offlinePrepIncludesProject,
} from "@/lib/field-reports/offline-prep-runner";
import { loadOpenIssuesCacheRecord } from "@/lib/field-reports/repositories/open-issues-repository";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

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

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

function readBackendSource(relativePath: string): string {
  return readFileSync(path.join(REPO_ROOT, relativePath), "utf8");
}

const ORG_ID = "org-zero-setup-z4";
const PROJECT_ID = "proj-zero-setup-z4";

describe("zero setup gate Z4", () => {
  beforeEach(async () => {
    vi.stubGlobal("localStorage", createLocalStorageMock());
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json({
          offline_max_days: 7,
          catalog_version: "z4-gate",
          catalog: { issues: [] },
          supervision_catalog: { issues: [], issue_count: 0 },
          public_areas: [{ id: "LOBBY", label_he: "לובי" }],
          apartments_by_project: {
            [PROJECT_ID]: [
              {
                id: "apt-1",
                organization_id: ORG_ID,
                project_id: PROJECT_ID,
                apartment_number: "1",
                group_key: "apartment:1",
                owner_name: "דייר",
                invite_status: "none",
              },
            ],
          },
          visit_types: [],
          organization_profile: {},
          projects: [{ id: PROJECT_ID, project_name: "Tower" }],
          reports: [],
          lines_storage_available: true,
        })
      )
    );
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
  });

  it("wires auto offline prep after project create", () => {
    const projectsPage = readSource("app/(dashboard)/projects/page.tsx");
    expect(projectsPage).toContain("ensureOfflinePrepForProject");
    expect(projectsPage).toContain("force: true");
  });

  it("wires auto offline prep on project workspace entry", () => {
    const workspaceHook = readSource("hooks/useProjectWorkspace.ts");
    expect(workspaceHook).toContain("ensureOfflinePrepForProject");
  });

  it("hook auto-prepares without manual button requirement", () => {
    const hook = readSource("hooks/useFieldReportOfflinePrep.ts");
    const newReportPage = readSource(
      "app/(dashboard)/projects/[id]/field-reports/new/page.tsx"
    );

    expect(hook).toContain("autoPrepare = true");
    expect(hook).toContain("autoPrepareAttemptedRef");
    expect(newReportPage).toContain("ensureOfflinePrepForProject");
    expect(newReportPage).not.toContain("בצע «הכנה לא מקוון»");
  });

  it("backend exposes project-scoped offline prep endpoint", () => {
    const main = readBackendSource("app/main.py");
    const service = readBackendSource(
      "app/services/field_visit_report_service.py"
    );

    expect(main).toContain('"/projects/{project_id}/offline-prep"');
    expect(service).toContain("build_offline_prep_bundle_for_project");
  });

  it("persists catalog and apartments in IndexedDB without manual click", async () => {
    const result = await fetchAndPersistOfflinePrepBundle({
      organizationId: ORG_ID,
      userId: "user-z4",
    });

    expect(result.bundle.catalog_version).toBe("z4-gate");
    expect(offlinePrepIncludesProject(result.bundle, PROJECT_ID)).toBe(true);

    const database = await getFieldReportDatabase();
    const catalogRecord = await database.get(FIELD_REPORT_STORES.catalog, ORG_ID);
    expect(catalogRecord?.catalog_version).toBe("z4-gate");
    expect(catalogRecord?.apartments_by_project?.[PROJECT_ID]).toHaveLength(1);
  });

  it("keeps open_issues store empty for a new project", async () => {
    await fetchAndPersistOfflinePrepBundle({
      organizationId: ORG_ID,
      userId: "user-z4",
    });

    const record = await loadOpenIssuesCacheRecord(ORG_ID);
    const snapshot = record?.projects[PROJECT_ID];

    expect(snapshot?.total).toBe(0);
    expect(snapshot?.items).toEqual([]);
  });

  it("ensureOfflinePrepForProject skips refetch when bundle already valid", async () => {
    let offlinePrepCalls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/field-reports/offline-prep")) {
          offlinePrepCalls += 1;
        }
        if (url.includes("/quality-issues/open")) {
          return Response.json({
            project_id: PROJECT_ID,
            total: 0,
            items: [],
          });
        }
        return Response.json({
          offline_max_days: 7,
          catalog_version: "z4-gate",
          catalog: { issues: [] },
          supervision_catalog: { issues: [], issue_count: 0 },
          public_areas: [],
          apartments_by_project: {
            [PROJECT_ID]: [
              {
                id: "apt-1",
                organization_id: ORG_ID,
                project_id: PROJECT_ID,
                apartment_number: "1",
                group_key: "apartment:1",
                owner_name: "דייר",
                invite_status: "none",
              },
            ],
          },
          visit_types: [],
          organization_profile: {},
          projects: [{ id: PROJECT_ID, project_name: "Tower" }],
          reports: [],
          lines_storage_available: true,
        });
      })
    );

    await ensureOfflinePrepForProject({
      organizationId: ORG_ID,
      projectId: PROJECT_ID,
      userId: "user-z4",
    });

    expect(offlinePrepCalls).toBe(1);

    await ensureOfflinePrepForProject({
      organizationId: ORG_ID,
      projectId: PROJECT_ID,
      userId: "user-z4",
    });

    expect(offlinePrepCalls).toBe(1);
  });
});
