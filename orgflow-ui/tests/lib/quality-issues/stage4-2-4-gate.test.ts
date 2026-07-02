import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  canContractorAccessRoute,
  isContractorDeniedRoute,
} from "@/lib/auth/contractor-route-guard";
import { isContractorLimitedProjectView } from "@/lib/auth/contractor-project-view";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 4.2.4 gate (contractor no field reports / catalog)", () => {
  it("denies contractor field report and portfolio routes", () => {
    expect(isContractorDeniedRoute("/field-reports/new")).toBe(true);
    expect(isContractorDeniedRoute("/portfolio")).toBe(true);
    expect(canContractorAccessRoute("CONTRACTOR", "/projects/p1/issues")).toBe(
      true
    );
    expect(isContractorLimitedProjectView("CONTRACTOR")).toBe(true);
  });

  it("wires contractor route guard and limited project overview", () => {
    const layout = readSource("app/(dashboard)/layout.tsx");
    const sidebar = readSource("components/layout/SidebarNavContent.tsx");
    const projectPage = readSource("app/(dashboard)/projects/[id]/page.tsx");
    const guard = readSource("components/auth/ContractorRouteGuard.tsx");
    const dashboard = readSource("components/projects/ProjectSupervisionDashboard.tsx");
    const settingsPage = readSource("app/(dashboard)/projects/[id]/settings/page.tsx");

    expect(layout).toContain("ContractorRouteGuard");
    expect(guard).toContain("contractorDeniedRouteRedirect");
    expect(sidebar).toContain("getQCPrimaryNavLinks");
    expect(sidebar).toContain("isContractorRole");
    expect(projectPage).toContain("contractorLimitedView");
    expect(dashboard).toContain("ProjectFieldReportLink");
    expect(settingsPage).toContain("ProjectDocumentsArchive");
  });
});
