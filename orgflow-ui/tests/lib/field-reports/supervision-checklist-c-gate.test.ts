/**
 * Gate — שלב C (field-supervision-checklist-spec §16.C).
 * זרימת יצירה מפרויקט + pickers + הסרת CTA + createSupervisionLocalReport.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("supervision checklist stage C gate (§16.C)", () => {
  it("project new report page exists with supervision pickers", () => {
    const page = readSource(
      "app/(dashboard)/projects/[id]/field-reports/new/page.tsx"
    );

    expect(page).toContain("ConstructionStagePicker");
    expect(page).toContain("VisitScopePicker");
    expect(page).toContain("ApartmentPicker");
    expect(page).toContain("PublicAreaPicker");
    expect(page).toContain("createSupervisionLocalReport");
    expect(page).toContain("התחל ביקור");
  });

  it("ProjectFieldReportLink points to project-scoped new route", () => {
    const link = readSource("components/field-reports/ProjectFieldReportLink.tsx");

    expect(link).toContain("projectFieldReportNewPath");
    expect(link).toContain("הפקת דוח");
    expect(link).not.toContain("/field-reports/new?project=");
  });

  it("field-reports list removed primary new-report CTA", () => {
    const listPage = readSource("app/(dashboard)/field-reports/page.tsx");

    expect(listPage).not.toContain('href="/field-reports/new"');
    expect(listPage).not.toContain("דוח ביקור חדש");
    expect(listPage).not.toContain("צור דוח ביקור ראשון");
  });

  it("supervision-new-report.ts creates local report with supervision_checklist", () => {
    const helper = readSource("lib/field-reports/supervision-new-report.ts");

    expect(helper).toContain("export async function createSupervisionLocalReport");
    expect(helper).toContain("buildSupervisionChecklist");
    expect(helper).toContain("supervision_meta");
    expect(helper).toContain("deriveVisitTypeFromConstructionStage");
  });

  it("picker components exist under components/field-reports/supervision", () => {
    for (const file of [
      "ConstructionStagePicker.tsx",
      "VisitScopePicker.tsx",
      "ApartmentPicker.tsx",
      "PublicAreaPicker.tsx",
    ]) {
      const source = readSource(
        `components/field-reports/supervision/${file}`
      );
      expect(source.length).toBeGreaterThan(0);
    }
  });

  it("legacy /field-reports/new redirects when project query is present", () => {
    const legacyPage = readSource("app/(dashboard)/field-reports/new/page.tsx");

    expect(legacyPage).toContain("preselectedProjectId");
    expect(legacyPage).toContain("router.replace");
    expect(legacyPage).toContain("/field-reports/new");
  });
});
