/**
 * Gate D7 — supervisor post-login lands on projects list.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  getSupervisionPrimaryNavLinks,
  recommendedPostLoginRoute,
  SUPERVISION_FIELD_REPORTS_ROUTE,
  SUPERVISION_PROJECTS_ROUTE,
} from "@/lib/qc-navigation";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("supervision dashboard D7 gate", () => {
  it("routes supervisor post-login to /projects", () => {
    expect(recommendedPostLoginRoute("SUPERVISOR")).toBe("/projects");
    expect(recommendedPostLoginRoute("SUPERVISOR")).toBe(
      SUPERVISION_PROJECTS_ROUTE.href
    );
  });

  it("keeps field reports in primary navigation", () => {
    const nav = getSupervisionPrimaryNavLinks({ role: "SUPERVISOR" });
    const hrefs = nav.map((link) => link.href);

    expect(hrefs).toContain(SUPERVISION_FIELD_REPORTS_ROUTE.href);
    expect(hrefs).toContain("/field-reports");
    expect(hrefs[0]).toBe("/projects");
  });

  it("documents supervisor landing in qc-navigation", () => {
    const navSource = readUiSource("lib/qc-navigation.ts");

    expect(navSource).toContain("recommendedPostLoginRoute");
    expect(navSource).toContain("SUPERVISION_PROJECTS_ROUTE.href");
    expect(navSource).not.toContain(
      'return SUPERVISION_FIELD_REPORTS_ROUTE.href'
    );
  });
});
