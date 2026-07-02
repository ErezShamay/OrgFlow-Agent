import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { GLOBAL_NAV_LINKS } from "@/lib/navigation";
import { getSupervisionPrimaryNavLinks } from "@/lib/qc-navigation";

const UI_ROOT = path.resolve(__dirname, "../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 5.1 gate (supervision primary navigation)", () => {
  it("GLOBAL_NAV_LINKS matches supervision primary nav structure", () => {
    const supervisorLinks = getSupervisionPrimaryNavLinks({ role: "SUPERVISOR" });
    expect(GLOBAL_NAV_LINKS).toEqual(supervisorLinks);
  });

  it("sidebar uses supervision primary nav for all personas", () => {
    const sidebar = readSource("components/layout/SidebarNavContent.tsx");

    expect(sidebar).toContain("getQCPrimaryNavLinks");
    expect(sidebar).toContain("isQCPrimaryNavActive");
    expect(sidebar).not.toContain("GLOBAL_NAV_LINKS");
    expect(sidebar).not.toContain("FIELD_REPORTS_ROUTE");
  });

  it("navigation.ts defines supervision routes without deprecated PM links", () => {
    const navigation = readSource("lib/navigation.ts");
    const hrefs = GLOBAL_NAV_LINKS.map((link) => link.href);

    expect(hrefs).toHaveLength(4);
    expect(hrefs).not.toContain("/operational-review");
    expect(hrefs).not.toContain("/upload");
    expect(hrefs).not.toContain("/actions");
    expect(hrefs).not.toContain("/reviews");
    expect(navigation).toContain("LEGACY_HOME_NAVBAR_LINKS");
  });
});
