/**
 * Gate D9 — public areas in apartment progress grid.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("supervision dashboard D9 gate", () => {
  it("renders public areas with visit CTA in progress grid", () => {
    const grid = readUiSource(
      "components/projects/ProjectApartmentProgressGrid.tsx"
    );
    const dashboard = readUiSource(
      "components/projects/ProjectSupervisionDashboard.tsx"
    );
    const lib = readUiSource("lib/projects/supervision-dashboard.ts");

    expect(grid).toContain("public_area");
    expect(grid).toContain("publicAreas");
    expect(grid).toContain("דירה ואזורים");
    expect(grid).toContain("תיעוד ביקור");
    expect(grid).toContain("projectSupervisionPublicAreaVisitReportPath");
    expect(dashboard).toContain("publicAreas={data.public_areas}");
    expect(lib).toContain("projectSupervisionPublicAreaVisitReportPath");
    expect(lib).toContain("public_area_id");
  });
});
