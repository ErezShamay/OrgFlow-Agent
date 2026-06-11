import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { GLOBAL_NAV_LINKS } from "@/lib/navigation";
import { getQCPrimaryNavLinks } from "@/lib/qc-navigation";

const UI_ROOT = path.resolve(__dirname, "../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 5.1 gate (QC primary navigation)", () => {
  it("GLOBAL_NAV_LINKS matches QC primary nav structure", () => {
    const supervisorLinks = getQCPrimaryNavLinks({ role: "SUPERVISOR" });
    expect(GLOBAL_NAV_LINKS).toEqual(supervisorLinks);
  });

  it("sidebar uses QC primary nav for all personas", () => {
    const sidebar = readSource("app/components/sidebar.tsx");

    expect(sidebar).toContain("getQCPrimaryNavLinks");
    expect(sidebar).toContain("isQCPrimaryNavActive");
    expect(sidebar).not.toContain("GLOBAL_NAV_LINKS");
    expect(sidebar).not.toContain("FIELD_REPORTS_ROUTE");
  });

  it("navigation.ts defines four QC routes without deprecated PM links", () => {
    const navigation = readSource("lib/navigation.ts");
    const hrefs = GLOBAL_NAV_LINKS.map((link) => link.href);

    expect(hrefs).toHaveLength(4);
    expect(hrefs).not.toContain("/upload");
    expect(hrefs).not.toContain("/actions");
    expect(hrefs).not.toContain("/reviews");
    expect(navigation).toContain("LEGACY_HOME_NAVBAR_LINKS");
  });
});
