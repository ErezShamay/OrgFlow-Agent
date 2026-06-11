import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("project visit issue diff UI gate (2.3.4)", () => {
  it("wires project diff summary into project overview page", () => {
    const projectPage = readUiSource(
      "app/(dashboard)/projects/[id]/page.tsx"
    );
    const summaryPanel = readUiSource(
      "components/quality-issues/ProjectVisitIssueDiffSummary.tsx"
    );
    const helpers = readUiSource(
      "lib/quality-issues/project-visit-issue-diff.ts"
    );
    const projectVisits = readUiSource("lib/field-reports/project-visits.ts");

    expect(projectPage).toContain("ProjectVisitIssueDiffSummary");
    expect(summaryPanel).toContain("loadProjectVisitIssueDiffSummaries");
    expect(summaryPanel).toContain("סיכום שינויי ליקויים");
    expect(summaryPanel).toContain("מעקב בין ביקורים");
    expect(helpers).toContain("selectRecentClosedVisitsForDiff");
    expect(helpers).toContain("summarizeProjectVisitDiffRows");
    expect(projectVisits).toContain("buildProjectFieldVisitsPath");
    expect(projectVisits).toContain("project_id");
  });
});
