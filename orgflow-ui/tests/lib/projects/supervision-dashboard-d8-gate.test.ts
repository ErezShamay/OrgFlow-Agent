/**
 * Gate D8 — project list health badges via batch supervision summaries.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

function readRepoSource(relativePath: string): string {
  return readFileSync(path.join(REPO_ROOT, relativePath), "utf8");
}

describe("supervision dashboard D8 gate", () => {
  it("exposes batch supervision summaries API", () => {
    const lib = readUiSource("lib/projects/supervision-dashboard.ts");
    const mainPy = readRepoSource("app/main.py");
    const service = readRepoSource(
      "app/services/project_supervision_dashboard_service.py"
    );

    expect(lib).toContain("fetchProjectSupervisionSummaries");
    expect(lib).toContain("/projects/supervision-summaries");
    expect(mainPy).toContain("/projects/supervision-summaries");
    expect(service).toContain("build_summaries_for_actor");
  });

  it("shows health badge on project list cards without per-card fetch", () => {
    const projectsPage = readUiSource("app/(dashboard)/projects/page.tsx");
    const card = readUiSource("components/projects/ProjectOverviewListCard.tsx");

    expect(projectsPage).toContain("fetchProjectSupervisionSummaries");
    expect(projectsPage).toContain("supervisionStatusByProjectId");
    expect(projectsPage).toContain("supervisionStatus=");
    expect(projectsPage).not.toContain("fetchProjectSupervisionDashboard(");
    expect(card).toContain("SUPERVISION_OVERALL_STATUS_LABELS");
    expect(card).toContain("supervisionStatus");
  });
});
