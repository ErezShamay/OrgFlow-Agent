import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  ADMIN_ONLY_SYSTEM_ROUTES,
  ADMIN_SYSTEM_NAV_LINKS,
  AUTOMATION_ROUTE,
  DEAD_LETTERS_ROUTE,
  getSystemNavLinks,
  isAdminOnlySystemRoute,
  SETTINGS_ROUTE,
} from "@/lib/navigation";
import { listSurfacesByCategory } from "@/lib/qc-freeze";

const UI_ROOT = path.resolve(__dirname, "../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 5.5 gate (automation admin-only)", () => {
  it("defines admin-only automation routes", () => {
    expect(ADMIN_ONLY_SYSTEM_ROUTES).toEqual([
      "/automation",
      "/automation/dead-letters",
    ]);
    expect(isAdminOnlySystemRoute("/automation")).toBe(true);
    expect(isAdminOnlySystemRoute("/automation/dead-letters")).toBe(true);
    expect(isAdminOnlySystemRoute("/automation/dead-letters/abc")).toBe(true);
    expect(isAdminOnlySystemRoute("/settings")).toBe(false);
  });

  it("shows automation links only in admin system nav", () => {
    const adminLinks = getSystemNavLinks(true);
    const userLinks = getSystemNavLinks(false);

    expect(adminLinks.map((link) => link.href)).toEqual([
      "/admin/users",
      "/settings",
      "/automation/dead-letters",
      "/automation",
    ]);
    expect(userLinks).toEqual([SETTINGS_ROUTE]);
    expect(userLinks.map((link) => link.href)).not.toContain("/automation");
    expect(userLinks.map((link) => link.href)).not.toContain(
      "/automation/dead-letters"
    );
    expect(ADMIN_SYSTEM_NAV_LINKS).toEqual([
      DEAD_LETTERS_ROUTE,
      AUTOMATION_ROUTE,
    ]);
  });

  it("aligns admin-only routes with qc-freeze ADMIN_ONLY surfaces", () => {
    const adminOnlyRoutes = listSurfacesByCategory("ADMIN_ONLY").flatMap(
      (surface) => surface.uiRoutes
    );

    for (const route of ADMIN_ONLY_SYSTEM_ROUTES) {
      expect(adminOnlyRoutes).toContain(route);
    }
  });

  it("protects automation pages with AdminGuard layout", () => {
    const layout = readSource("app/(dashboard)/automation/layout.tsx");

    expect(layout).toContain("AdminGuard");
    expect(
      existsSync(path.join(UI_ROOT, "app/(dashboard)/automation/layout.tsx"))
    ).toBe(true);
  });

  it("wires admin-filtered system nav in sidebar", () => {
    const sidebar = readSource("components/layout/SidebarNavContent.tsx");
    const systemNav = readSource("components/layout/SystemNavDropdown.tsx");

    expect(sidebar).toContain("getSystemNavLinks(isAdminUser");
    expect(systemNav).toContain("getSystemNavLinks(isAdminUser)");
  });
});
