import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  GLOBAL_NAV_LINKS,
  HOME_NAVBAR_LINKS,
  PRIMARY_NAV_HIDDEN_ROUTES,
  UPLOAD_LEGACY_ROUTE,
} from "@/lib/navigation";
import { getQCPrimaryNavLinks } from "@/lib/qc-navigation";
import { shouldHideFromPrimaryNav } from "@/lib/qc-freeze";

const UI_ROOT = path.resolve(__dirname, "../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 5.2 gate (hide /upload from primary nav)", () => {
  it("marks /upload as hidden and aligned with qc-freeze", () => {
    expect(PRIMARY_NAV_HIDDEN_ROUTES).toContain("/upload");
    expect(shouldHideFromPrimaryNav("/upload")).toBe(true);
    expect(UPLOAD_LEGACY_ROUTE.href).toBe("/upload");
  });

  it("excludes /upload from dashboard and home primary nav", () => {
    const supervisorLinks = getQCPrimaryNavLinks({ role: "SUPERVISOR" });

    expect(GLOBAL_NAV_LINKS.map((link) => link.href)).not.toContain("/upload");
    expect(HOME_NAVBAR_LINKS.map((link) => link.href)).not.toContain("/upload");
    expect(supervisorLinks.map((link) => link.href)).not.toContain("/upload");
  });

  it("keeps upload page reachable by direct URL", () => {
    expect(
      existsSync(path.join(UI_ROOT, "app/(dashboard)/upload/page.tsx"))
    ).toBe(true);
  });

  it("removes upload CTA from project documents empty state", () => {
    const archive = readSource("components/projects/ProjectDocumentsArchive.tsx");

    expect(archive).not.toContain("העלאת דוח");
    expect(archive).toContain("דוח שטח");
  });
});
