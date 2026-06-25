/**
 * Gate D4 — project page shows supervision dashboard for supervisors.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { canViewProjectSupervisionDashboard } from "@/lib/projects/supervision-dashboard";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("supervision dashboard D4 gate", () => {
  it("shows dashboard on project page for supervision roles", () => {
    const projectPage = readUiSource("app/(dashboard)/projects/[id]/page.tsx");

    expect(projectPage).toContain("ProjectSupervisionDashboard");
    expect(projectPage).toContain("canViewProjectSupervisionDashboard");
    expect(projectPage).toContain("showSupervisionDashboard");
    expect(projectPage).toContain("ProjectVisitIssueDiffSummary");
    expect(canViewProjectSupervisionDashboard("ADMIN")).toBe(true);
    expect(canViewProjectSupervisionDashboard("SUPERVISOR")).toBe(true);
  });

  it("moves project details editor to settings page", () => {
    const settingsPage = readUiSource(
      "app/(dashboard)/projects/[id]/settings/page.tsx"
    );
    const dashboard = readUiSource(
      "components/projects/ProjectSupervisionDashboard.tsx"
    );

    expect(
      existsSync(
        path.join(UI_ROOT, "app/(dashboard)/projects/[id]/settings/page.tsx")
      )
    ).toBe(true);
    expect(settingsPage).toContain("ProjectDetailsEditor");
    expect(settingsPage).toContain("הגדרות פרויקט");
    expect(settingsPage).toContain("ProjectDocumentsArchive");
    expect(settingsPage).toContain("ProjectActivityTimeline");
    expect(dashboard).toContain("הגדרות פרויקט");
    expect(dashboard).toContain("/settings");
  });

  it("keeps links to issues and field reports on dashboard", () => {
    const dashboard = readUiSource(
      "components/projects/ProjectSupervisionDashboard.tsx"
    );

    expect(dashboard).toContain("כל הליקויים");
    expect(dashboard).toContain("/issues");
    expect(dashboard).toContain("דוחות שטח");
    expect(dashboard).toContain("ProjectFieldReportLink");
    expect(dashboard).toContain("projectFieldReportsListPath");
  });

  it("keeps contractor limited project view separate from dashboard", () => {
    const projectPage = readUiSource("app/(dashboard)/projects/[id]/page.tsx");

    expect(projectPage).toContain("isContractorLimitedProjectView");
    expect(projectPage).toContain("contractorLimitedView");
    expect(canViewProjectSupervisionDashboard("CONTRACTOR")).toBe(false);
  });
});
