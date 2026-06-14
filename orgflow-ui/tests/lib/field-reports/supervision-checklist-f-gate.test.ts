/**
 * Gate — שלב F (field-supervision-checklist-spec §16.F).
 * Offline prep + דירות בחבילה + יצירת דוח מלא offline.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

function readBackendSource(relativePath: string): string {
  return readFileSync(path.join(REPO_ROOT, relativePath), "utf8");
}

describe("supervision checklist stage F gate (§16.F)", () => {
  it("offline prep bundle types include apartments and supervision catalog", () => {
    const types = readSource("lib/field-reports/offline-store-types.ts");

    expect(types).toContain("apartments_by_project");
    expect(types).toContain("supervision_catalog");
    expect(types).toContain("public_areas");
  });

  it("backend build_offline_prep_bundle adds supervision offline fields", () => {
    const service = readBackendSource(
      "app/services/field_visit_report_service.py"
    );
    const helper = readBackendSource(
      "app/services/field_supervision_offline_bundle.py"
    );

    expect(service).toContain("supervision_catalog");
    expect(service).toContain("apartments_by_project");
    expect(service).toContain("public_areas");
    expect(helper).toContain("build_supervision_catalog");
    expect(helper).toContain("build_apartments_by_project");
  });

  it("ApartmentPicker loads offline apartments from bundle", () => {
    const picker = readSource(
      "components/field-reports/supervision/ApartmentPicker.tsx"
    );
    const helper = readSource("lib/field-reports/offline-prep-apartments.ts");

    expect(picker).toContain("offlineApartments");
    expect(helper).toContain("listApartmentsFromOfflineBundle");
  });

  it("new report page wires offline apartments into ApartmentPicker", () => {
    const page = readSource(
      "app/(dashboard)/projects/[id]/field-reports/new/page.tsx"
    );

    expect(page).toContain("listApartmentsFromOfflineBundle");
    expect(page).toContain("offlineApartments=");
  });

  it("supervision catalog prefers dedicated supervision_catalog field", () => {
    const catalog = readSource("lib/field-reports/supervision-catalog.ts");

    expect(catalog).toContain("bundle.supervision_catalog");
  });
});
