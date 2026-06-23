/**
 * Gate D10 — E2E wiring for project supervision dashboard.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

const GATE_TESTS = [
  "tests/lib/projects/supervision-dashboard-d3-gate.test.ts",
  "tests/lib/projects/supervision-dashboard-d4-gate.test.ts",
  "tests/lib/projects/supervision-dashboard-d5-gate.test.ts",
  "tests/lib/projects/supervision-dashboard-d6-gate.test.ts",
  "tests/lib/projects/supervision-dashboard-d7-gate.test.ts",
  "tests/lib/projects/supervision-dashboard-d8-gate.test.ts",
  "tests/lib/projects/supervision-dashboard-d9-gate.test.ts",
] as const;

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("supervision dashboard D10 e2e gate", () => {
  it("includes pytest E2E for dashboard KPI + trade detail + summaries", () => {
    const e2e = readFileSync(
      path.join(REPO_ROOT, "tests/test_project_supervision_dashboard_e2e.py"),
      "utf8"
    );

    expect(existsSync(path.join(REPO_ROOT, "tests/test_project_supervision_dashboard_e2e.py"))).toBe(true);
    expect(e2e).toContain("supervision-dashboard");
    expect(e2e).toContain("supervision-summaries");
    expect(e2e).toContain("supervision-dashboard/trades/electrical");
    expect(e2e).toContain('progress_percent"] == 50');
  });

  it("wires full UI stack from dashboard through visit prefill", () => {
    const dashboard = readUiSource("components/projects/ProjectSupervisionDashboard.tsx");
    const grid = readUiSource("components/projects/ProjectApartmentProgressGrid.tsx");
    const newReport = readUiSource(
      "app/(dashboard)/projects/[id]/field-reports/new/page.tsx"
    );
    const nav = readUiSource("lib/qc-navigation.ts");

    expect(dashboard).toContain("ProjectSupervisionKpiRow");
    expect(grid).toContain("תיעוד ביקור");
    expect(newReport).toContain("parseSupervisionNewReportPrefill");
    expect(nav).toContain('return SUPERVISION_PROJECTS_ROUTE.href');
  });

  it("registers D3–D9 vitest gate files", () => {
    for (const gatePath of GATE_TESTS) {
      expect(existsSync(path.join(UI_ROOT, gatePath))).toBe(true);
    }
  });
});
