import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(relativePath: string, root = UI_ROOT): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

describe("stage 4.1.1 gate (open issues per project KPI)", () => {
  it("ships backend KPI helpers and API wiring", () => {
    const kpiModule = readSource(
      "app/services/quality_issue_portfolio_kpi.py",
      REPO_ROOT
    );
    const service = readSource(
      "app/services/quality_issue_service.py",
      REPO_ROOT
    );

    expect(kpiModule).toContain("build_open_issues_per_project_summaries");
    expect(service).toContain("build_open_issues_per_project_summaries");
    expect(service).toContain("get_portfolio_quality_summary");
  });

  it("shows per-project open issues in portfolio QC panel", () => {
    const panel = readSource(
      "components/quality-issues/PortfolioQualitySummaryPanel.tsx"
    );
    const ranking = readSource(
      "components/quality-issues/PortfolioProjectRanking.tsx"
    );
    const helpers = readSource("lib/quality-issues/portfolio-summary.ts");

    expect(panel).toContain("formatOpenIssuesPerProjectCaption");
    expect(panel).toContain("total_open");
    expect(ranking).toContain("rankProjectsByQcPressure");
    expect(ranking).toContain("open_total");
    expect(helpers).toContain("countProjectsWithOpenIssues");
  });
});
