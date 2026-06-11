import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  ACTIONS_LEGACY_ROUTE,
  ESCALATIONS_LEGACY_ROUTE,
  GLOBAL_NAV_LINKS,
  HOME_NAVBAR_LINKS,
  PRIMARY_NAV_HIDDEN_ROUTES,
} from "@/lib/navigation";
import { getQCPrimaryNavLinks, getQCProjectNavLinks } from "@/lib/qc-navigation";
import { shouldHideFromPrimaryNav } from "@/lib/qc-freeze";

const UI_ROOT = path.resolve(__dirname, "../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 5.3 gate (hide /actions and /escalations from primary nav)", () => {
  it("marks actions and escalations as hidden and aligned with qc-freeze", () => {
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/actions");
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/escalations");
    expect(shouldHideFromPrimaryNav(ACTIONS_LEGACY_ROUTE.href)).toBe(true);
    expect(shouldHideFromPrimaryNav(ESCALATIONS_LEGACY_ROUTE.href)).toBe(true);
  });

  it("excludes actions and escalations from dashboard and home primary nav", () => {
    const supervisorLinks = getQCPrimaryNavLinks({ role: "SUPERVISOR" });
    const homeHrefs = HOME_NAVBAR_LINKS.map((link) => link.href);
    const globalHrefs = GLOBAL_NAV_LINKS.map((link) => link.href);

    expect(globalHrefs).not.toContain("/actions");
    expect(globalHrefs).not.toContain("/escalations");
    expect(homeHrefs).not.toContain("/actions");
    expect(homeHrefs).not.toContain("/escalations");
    expect(supervisorLinks.map((link) => link.href)).not.toContain("/actions");
    expect(supervisorLinks.map((link) => link.href)).not.toContain(
      "/escalations"
    );
    expect(supervisorLinks.map((link) => link.href)).toContain("/issues");
  });

  it("keeps legacy pages reachable by direct URL", () => {
    expect(
      existsSync(path.join(UI_ROOT, "app/(dashboard)/actions/page.tsx"))
    ).toBe(true);
    expect(
      existsSync(path.join(UI_ROOT, "app/(dashboard)/escalations/page.tsx"))
    ).toBe(true);
  });

  it("removes actions and escalations from QC project nav", () => {
    const projectNav = getQCProjectNavLinks("proj-1", "SUPERVISOR");
    const labels = projectNav.map((link) => link.label);
    const hrefs = projectNav.map((link) => link.href);

    expect(labels).toContain("ליקויים");
    expect(labels).not.toContain("פעולות תפעוליות");
    expect(labels).not.toContain("נקודות סיכון");
    expect(hrefs).not.toContain("/projects/proj-1/actions");
    expect(hrefs).not.toContain("/projects/proj-1/escalations");
  });

  it("wires project tabs to QC project nav without legacy PM tabs", () => {
    const projectTabs = readSource("app/components/project-tabs.tsx");

    expect(projectTabs).toContain("getQCProjectNavLinks");
    expect(projectTabs).not.toContain("/escalations");
    expect(projectTabs).not.toContain("/actions");
  });
});
