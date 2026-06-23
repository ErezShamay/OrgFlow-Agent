import { describe, expect, it } from "vitest";

import {
  ACTIONS_LEGACY_ROUTE,
  ADMIN_SYSTEM_NAV_LINKS,
  AUTOMATION_ROUTE,
  DEAD_LETTERS_ROUTE,
  PLATFORM_ADMIN_HOME_ROUTE,
  PLATFORM_ADMIN_NAV_LINKS,
  POST_LOGIN_ROUTE,
  ESCALATIONS_LEGACY_ROUTE,
  FIELD_REPORTS_ROUTE,
  filterPrimaryNavLinks,
  getSystemNavLinks,
  GLOBAL_NAV_LINKS,
  HOME_NAVBAR_LINKS,
  isAdminOnlySystemRoute,
  LEGACY_HOME_NAVBAR_LINKS,
  PRIMARY_NAV_HIDDEN_ROUTES,
  REVIEWS_GLOBAL_LEGACY_ROUTE,
  resolvePostLoginRoute,
  SETTINGS_ROUTE,
  UPLOAD_LEGACY_ROUTE,
} from "@/lib/navigation";
import { shouldHideFromPrimaryNav } from "@/lib/qc-freeze";

describe("navigation (supervision pivot — stage A)", () => {
  it("defines supervision items in GLOBAL_NAV_LINKS without operational review", () => {
    expect(GLOBAL_NAV_LINKS).toHaveLength(4);
    expect(GLOBAL_NAV_LINKS.map((link) => link.label)).toEqual([
      "סקירת הפרויקטים",
      "דוחות שטח",
      "ליקויים",
      "תיק פיקוח הנדסי",
    ]);
    expect(GLOBAL_NAV_LINKS.map((link) => link.href)).toEqual([
      "/projects",
      "/field-reports",
      "/issues",
      "/portfolio",
    ]);
  });

  it("uses project overview as first nav item", () => {
    expect(GLOBAL_NAV_LINKS[0]).toEqual({
      href: "/projects",
      label: "סקירת הפרויקטים",
    });
  });

  it("keeps remaining legacy PM links on public home navbar until stage 5.8", () => {
    expect(HOME_NAVBAR_LINKS).toEqual(LEGACY_HOME_NAVBAR_LINKS);
    expect(HOME_NAVBAR_LINKS.map((link) => link.href)).not.toContain("/issues");
    expect(HOME_NAVBAR_LINKS.map((link) => link.label)).toContain("מנהל דיירים");
  });

  it("hides upload from all primary nav surfaces (stage 5.2)", () => {
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/upload");
    expect(shouldHideFromPrimaryNav(UPLOAD_LEGACY_ROUTE.href)).toBe(true);
    expect(GLOBAL_NAV_LINKS.map((link) => link.href)).not.toContain("/upload");
    expect(HOME_NAVBAR_LINKS.map((link) => link.href)).not.toContain("/upload");
    expect(
      filterPrimaryNavLinks([
        UPLOAD_LEGACY_ROUTE,
        FIELD_REPORTS_ROUTE,
      ]).map((link) => link.href)
    ).toEqual(["/field-reports"]);
  });

  it("hides actions and escalations from primary nav (stage 5.3)", () => {
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/upload");
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/actions");
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/escalations");
    expect(shouldHideFromPrimaryNav(ACTIONS_LEGACY_ROUTE.href)).toBe(true);
    expect(shouldHideFromPrimaryNav(ESCALATIONS_LEGACY_ROUTE.href)).toBe(true);
    expect(GLOBAL_NAV_LINKS.map((link) => link.href)).not.toContain("/actions");
    expect(GLOBAL_NAV_LINKS.map((link) => link.href)).not.toContain(
      "/escalations"
    );
    expect(HOME_NAVBAR_LINKS.map((link) => link.href)).not.toContain("/actions");
    expect(HOME_NAVBAR_LINKS.map((link) => link.href)).not.toContain(
      "/escalations"
    );
    expect(HOME_NAVBAR_LINKS.map((link) => link.label)).not.toContain(
      "פעולות תפעוליות"
    );
    expect(HOME_NAVBAR_LINKS.map((link) => link.label)).not.toContain(
      "נקודות סיכון"
    );
  });

  it("hides global reviews from primary nav (stage 5.4)", () => {
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/reviews");
    expect(shouldHideFromPrimaryNav(REVIEWS_GLOBAL_LEGACY_ROUTE.href)).toBe(
      true
    );
    expect(GLOBAL_NAV_LINKS.map((link) => link.href)).not.toContain("/reviews");
    expect(HOME_NAVBAR_LINKS.map((link) => link.href)).not.toContain("/reviews");
    expect(HOME_NAVBAR_LINKS.map((link) => link.label)).not.toContain(
      "ביקורות AI"
    );
  });

  it("limits automation system nav to admin only (stage 5.5)", () => {
    expect(getSystemNavLinks(false)).toEqual([SETTINGS_ROUTE]);
    expect(getSystemNavLinks(true).map((link) => link.href)).toContain(
      "/automation"
    );
    expect(getSystemNavLinks(true).map((link) => link.href)).toContain(
      "/automation/dead-letters"
    );
    expect(ADMIN_SYSTEM_NAV_LINKS).toEqual([
      DEAD_LETTERS_ROUTE,
      AUTOMATION_ROUTE,
    ]);
    expect(isAdminOnlySystemRoute("/automation/runs")).toBe(true);
    expect(isAdminOnlySystemRoute("/portfolio")).toBe(false);
  });

  it("routes users after login by role", () => {
    expect(resolvePostLoginRoute("PLATFORM_ADMIN")).toBe(
      PLATFORM_ADMIN_HOME_ROUTE.href
    );
    expect(resolvePostLoginRoute("SUPERVISOR")).toBe("/projects");
    expect(resolvePostLoginRoute("ADMIN")).toBe("/projects");
    expect(POST_LOGIN_ROUTE).toBe("/projects");
    expect(PLATFORM_ADMIN_NAV_LINKS[0]).toEqual(PLATFORM_ADMIN_HOME_ROUTE);
  });

  it("prioritizes platform admin system navigation", () => {
    expect(
      getSystemNavLinks(true, { platformAdmin: true }).map(
        (link) => link.href
      )
    ).toEqual([
      "/admin/platform",
      "/admin/users",
      "/settings",
      "/automation/dead-letters",
      "/automation",
    ]);
  });
});
