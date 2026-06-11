import { describe, expect, it } from "vitest";

import {
  QC_DEPRECATED_PRIMARY_ROUTES,
  QC_PRIMARY_NAV_ITEMS,
  getQCPrimaryNavLinks,
  getQCProjectNavLinks,
  getQCProjectPrimaryNavLinks,
  getQCProjectSecondaryNavLinks,
  isQCPrimaryNavActive,
  isQCProjectNavActive,
  recommendedPostLoginRoute,
} from "@/lib/qc-navigation";

describe("qc navigation (spec 0.4)", () => {
  it("defines exactly four primary nav items", () => {
    expect(QC_PRIMARY_NAV_ITEMS).toHaveLength(4);
    expect(QC_PRIMARY_NAV_ITEMS.map((item) => item.label)).toEqual([
      "תיק QC",
      "פרויקטים",
      "דוחות שטח",
      "ליקויים",
    ]);
  });

  it("lists deprecated PM routes for removal from primary nav", () => {
    const hrefs = QC_DEPRECATED_PRIMARY_ROUTES.map((item) => item.href);
    expect(hrefs).toContain("/upload");
    expect(hrefs).toContain("/actions");
    expect(hrefs).toContain("/reviews");
    expect(hrefs).not.toContain("/portfolio");
  });

  it("shows full primary nav for supervisor", () => {
    const links = getQCPrimaryNavLinks({ role: "SUPERVISOR" });
    expect(links).toHaveLength(4);
    expect(links.map((link) => link.href)).toEqual([
      "/portfolio",
      "/projects",
      "/field-reports",
      "/issues",
    ]);
  });

  it("hides field reports and portfolio for contractor", () => {
    const links = getQCPrimaryNavLinks({ role: "CONTRACTOR" });
    expect(links.map((link) => link.href)).toEqual(["/projects", "/issues"]);
  });

  it("hides field reports write nav for developer but keeps portfolio", () => {
    const links = getQCPrimaryNavLinks({ role: "DEVELOPER" });
    expect(links.map((link) => link.label)).toEqual([
      "תיק QC",
      "פרויקטים",
      "דוחות שטח",
      "ליקויים",
    ]);
  });

  it("omits field reports when module disabled", () => {
    const links = getQCPrimaryNavLinks({
      role: "SUPERVISOR",
      fieldReportsEnabled: false,
    });
    expect(links.map((link) => link.href)).not.toContain("/field-reports");
    expect(links).toHaveLength(3);
  });

  it("builds project nav without operational actions", () => {
    const links = getQCProjectNavLinks("proj-1", "SUPERVISOR");
    const labels = links.map((link) => link.label);
    expect(labels).toContain("ליקויים");
    expect(labels).toContain("ביקורות AI");
    expect(labels).not.toContain("פעולות תפעוליות");
    expect(labels).not.toContain("נקודות סיכון");
  });

  it("splits project reviews into secondary nav (stage 5.4)", () => {
    const primary = getQCProjectPrimaryNavLinks("proj-1", "SUPERVISOR");
    const secondary = getQCProjectSecondaryNavLinks("proj-1", "SUPERVISOR");

    expect(primary.map((link) => link.label)).toEqual([
      "סקירת הפרויקט",
      "ליקויים",
    ]);
    expect(secondary.map((link) => link.href)).toEqual([
      "/projects/proj-1/reviews",
    ]);
    expect(secondary.map((link) => link.label)).toEqual(["ביקורות AI"]);
  });

  it("hides secondary reviews for developer persona", () => {
    expect(getQCProjectSecondaryNavLinks("proj-1", "DEVELOPER")).toEqual([]);
    expect(
      getQCProjectPrimaryNavLinks("proj-1", "DEVELOPER").map((link) => link.label)
    ).toEqual(["סקירת הפרויקט", "ליקויים"]);
  });

  it("limits contractor project nav to overview and issues", () => {
    const links = getQCProjectNavLinks("proj-1", "CONTRACTOR");
    expect(links.map((link) => link.label)).toEqual([
      "סקירת הפרויקט",
      "ליקויים",
    ]);
  });

  it("detects active project nav paths without matching overview on child routes", () => {
    expect(
      isQCProjectNavActive("/projects/proj-1", "/projects/proj-1")
    ).toBe(true);
    expect(
      isQCProjectNavActive(
        "/projects/proj-1/issues",
        "/projects/proj-1"
      )
    ).toBe(false);
    expect(
      isQCProjectNavActive(
        "/projects/proj-1/issues/issue-1",
        "/projects/proj-1/issues"
      )
    ).toBe(true);
  });

  it("detects active primary nav paths", () => {
    expect(isQCPrimaryNavActive("/portfolio", "/portfolio")).toBe(true);
    expect(isQCPrimaryNavActive("/portfolio/extra", "/portfolio")).toBe(false);
    expect(isQCPrimaryNavActive("/projects/abc", "/projects")).toBe(true);
    expect(isQCPrimaryNavActive("/projects/abc/reviews", "/projects")).toBe(
      false
    );
    expect(isQCPrimaryNavActive("/issues/123", "/issues")).toBe(true);
  });

  it("recommends post-login route by persona", () => {
    expect(recommendedPostLoginRoute("CONTRACTOR")).toBe("/issues");
    expect(recommendedPostLoginRoute("SUPERVISOR")).toBe("/portfolio");
    expect(recommendedPostLoginRoute("DEVELOPER")).toBe("/portfolio");
  });
});
