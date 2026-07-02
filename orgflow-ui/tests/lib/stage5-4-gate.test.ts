import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  GLOBAL_NAV_LINKS,
  HOME_NAVBAR_LINKS,
  PRIMARY_NAV_HIDDEN_ROUTES,
  REVIEWS_GLOBAL_LEGACY_ROUTE,
} from "@/lib/navigation";
import { getSupervisionPrimaryNavLinks } from "@/lib/qc-navigation";
import { shouldHideFromPrimaryNav } from "@/lib/qc-freeze";

const UI_ROOT = path.resolve(__dirname, "../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 5.4 gate (reviews hidden in supervision v1)", () => {
  it("marks global /reviews as hidden and aligned with qc-freeze", () => {
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/reviews");
    expect(shouldHideFromPrimaryNav(REVIEWS_GLOBAL_LEGACY_ROUTE.href)).toBe(
      true
    );
  });

  it("excludes /reviews from dashboard and home primary nav", () => {
    const supervisorLinks = getSupervisionPrimaryNavLinks({ role: "SUPERVISOR" });

    expect(GLOBAL_NAV_LINKS.map((link) => link.href)).not.toContain("/reviews");
    expect(HOME_NAVBAR_LINKS.map((link) => link.href)).not.toContain("/reviews");
    expect(supervisorLinks.map((link) => link.href)).not.toContain("/reviews");
  });

  it("keeps global reviews page reachable by direct URL only", () => {
    expect(
      existsSync(path.join(UI_ROOT, "app/(dashboard)/reviews/page.tsx"))
    ).toBe(true);
  });

  it("hides project reviews from nav in supervision v1", () => {
    const sidebar = readSource("components/layout/SidebarNavContent.tsx");
    expect(sidebar).toContain("getQCProjectPrimaryNavLinks");
    expect(sidebar).not.toContain('label: "ביקורות AI"');
  });
});
