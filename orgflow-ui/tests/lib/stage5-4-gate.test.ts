import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  GLOBAL_NAV_LINKS,
  HOME_NAVBAR_LINKS,
  PRIMARY_NAV_HIDDEN_ROUTES,
  REVIEWS_GLOBAL_LEGACY_ROUTE,
} from "@/lib/navigation";
import {
  getQCPrimaryNavLinks,
  getQCProjectSecondaryNavLinks,
} from "@/lib/qc-navigation";
import { shouldHideFromPrimaryNav } from "@/lib/qc-freeze";

const UI_ROOT = path.resolve(__dirname, "../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 5.4 gate (global /reviews hidden, project secondary tab only)", () => {
  it("marks global /reviews as hidden and aligned with qc-freeze", () => {
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/reviews");
    expect(shouldHideFromPrimaryNav(REVIEWS_GLOBAL_LEGACY_ROUTE.href)).toBe(
      true
    );
  });

  it("excludes /reviews from dashboard and home primary nav", () => {
    const supervisorLinks = getQCPrimaryNavLinks({ role: "SUPERVISOR" });

    expect(GLOBAL_NAV_LINKS.map((link) => link.href)).not.toContain("/reviews");
    expect(HOME_NAVBAR_LINKS.map((link) => link.href)).not.toContain("/reviews");
    expect(supervisorLinks.map((link) => link.href)).not.toContain("/reviews");
  });

  it("keeps global reviews page reachable by direct URL", () => {
    expect(
      existsSync(path.join(UI_ROOT, "app/(dashboard)/reviews/page.tsx"))
    ).toBe(true);
  });

  it("exposes project reviews only in secondary nav", () => {
    const secondary = getQCProjectSecondaryNavLinks("proj-1", "SUPERVISOR");

    expect(secondary).toEqual([
      {
        href: "/projects/proj-1/reviews",
        label: "ביקורות AI",
      },
    ]);
  });

  it("wires sidebar secondary project section for reviews", () => {
    const sidebar = readSource("app/components/sidebar.tsx");

    expect(sidebar).toContain("getQCProjectSecondaryNavLinks");
    expect(sidebar).toContain("משני בפרויקט");
    expect(sidebar).toContain("getQCProjectPrimaryNavLinks");
  });
});
