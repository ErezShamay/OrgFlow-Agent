import { describe, expect, it } from "vitest";

import {
  SUPERVISION_DEPRECATED_PRIMARY_ROUTES,
  SUPERVISION_PRIMARY_NAV_ITEMS,
  getSupervisionPrimaryNavLinks,
  getSupervisionProjectNavLinks,
  getSupervisionProjectPrimaryNavLinks,
  getSupervisionProjectSecondaryNavLinks,
  isSupervisionPrimaryNavActive,
  isSupervisionProjectNavActive,
  recommendedPostLoginRoute,
} from "@/lib/qc-navigation";

describe("supervision navigation (PRODUCT-SPEC-LOCKED §11)", () => {
  it("defines primary nav without operational review", () => {
    expect(SUPERVISION_PRIMARY_NAV_ITEMS).toHaveLength(4);
    expect(SUPERVISION_PRIMARY_NAV_ITEMS.map((item) => item.label)).toEqual([
      "סקירת הפרויקטים",
      "דוחות שטח",
      "ליקויים",
      "תיק פיקוח הנדסי",
    ]);
  });

  it("lists deprecated OUT routes including operational review", () => {
    const hrefs = SUPERVISION_DEPRECATED_PRIMARY_ROUTES.map((item) => item.href);
    expect(hrefs).toContain("/upload");
    expect(hrefs).toContain("/actions");
    expect(hrefs).toContain("/reviews");
    expect(hrefs).toContain("/operational-review");
    expect(hrefs).not.toContain("/portfolio");
  });

  it("shows supervision nav for supervisor", () => {
    const links = getSupervisionPrimaryNavLinks({ role: "SUPERVISOR" });
    expect(links).toHaveLength(4);
    expect(links.map((link) => link.href)).toEqual([
      "/projects",
      "/field-reports",
      "/issues",
      "/portfolio",
    ]);
  });

  it("hides primary nav for contractor (disabled v1 persona)", () => {
    const links = getSupervisionPrimaryNavLinks({ role: "CONTRACTOR" });
    expect(links).toEqual([]);
  });

  it("hides primary nav for developer (disabled v1 persona)", () => {
    const links = getSupervisionPrimaryNavLinks({ role: "DEVELOPER" });
    expect(links).toEqual([]);
  });

  it("omits field reports when module disabled", () => {
    const links = getSupervisionPrimaryNavLinks({
      role: "SUPERVISOR",
      fieldReportsEnabled: false,
    });
    expect(links.map((link) => link.href)).not.toContain("/field-reports");
    expect(links).toHaveLength(3);
  });

  it("builds project nav without reviews AI", () => {
    const links = getSupervisionProjectNavLinks("proj-1", "SUPERVISOR");
    const labels = links.map((link) => link.label);
    expect(labels).toEqual(["סקירה", "ליקויים", "דיירים"]);
    expect(labels).not.toContain("ביקורות AI");
  });

  it("has no secondary project nav in supervision v1", () => {
    expect(getSupervisionProjectSecondaryNavLinks("proj-1", "SUPERVISOR")).toEqual(
      []
    );
    expect(getSupervisionProjectPrimaryNavLinks("proj-1", "SUPERVISOR").map(
      (link) => link.label
    )).toEqual(["סקירה", "ליקויים", "דיירים"]);
  });

  it("hides project nav for contractor", () => {
    expect(getSupervisionProjectNavLinks("proj-1", "CONTRACTOR")).toEqual([]);
  });

  it("detects active project nav paths", () => {
    expect(
      isSupervisionProjectNavActive("/projects/proj-1", "/projects/proj-1")
    ).toBe(true);
    expect(
      isSupervisionProjectNavActive(
        "/projects/proj-1/issues",
        "/projects/proj-1"
      )
    ).toBe(false);
  });

  it("detects active primary nav paths", () => {
    expect(isSupervisionPrimaryNavActive("/portfolio", "/portfolio")).toBe(true);
    expect(isSupervisionPrimaryNavActive("/issues/123", "/issues")).toBe(true);
  });

  it("recommends post-login route by role", () => {
    expect(recommendedPostLoginRoute("SUPERVISOR")).toBe("/projects");
    expect(recommendedPostLoginRoute("ADMIN")).toBe("/projects");
    expect(recommendedPostLoginRoute("MANAGER")).toBe("/projects");
    expect(recommendedPostLoginRoute("CONTRACTOR")).toBe("/projects");
    expect(recommendedPostLoginRoute("DEVELOPER")).toBe("/projects");
    expect(recommendedPostLoginRoute("PLATFORM_ADMIN")).toBe("/admin/platform");
  });
});
