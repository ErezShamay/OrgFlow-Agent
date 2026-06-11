import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(relativePath: string, root = UI_ROOT): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

describe("stage 4.1.5 gate (QC project ranking)", () => {
  it("ships backend QC ranking helpers and API ordering", () => {
    const kpiModule = readSource(
      "app/services/quality_issue_portfolio_kpi.py",
      REPO_ROOT
    );
    const service = readSource(
      "app/services/quality_issue_service.py",
      REPO_ROOT
    );

    expect(kpiModule).toContain("rank_portfolio_projects_by_qc_pressure");
    expect(kpiModule).toContain("open_critical");
    expect(kpiModule).toContain("open_total");
    expect(service).toContain("build_open_issues_per_project_summaries");
  });

  it("shows QC project ranking as primary on portfolio page", () => {
    const ranking = readSource(
      "components/quality-issues/PortfolioProjectRanking.tsx"
    );
    const portfolioPage = readSource("app/(dashboard)/portfolio/page.tsx");
    const legacySection = readSource(
      "components/quality-issues/PortfolioLegacySection.tsx"
    );
    const helpers = readSource("lib/quality-issues/portfolio-summary.ts");

    expect(ranking).toContain("rankProjectsByQcPressure");
    expect(ranking).toContain("דירוג פרויקטים");
    expect(ranking).toContain("open_critical");
    expect(ranking).toContain("open_total");
    expect(portfolioPage).toContain("PortfolioProjectRanking");
    expect(legacySection).toContain("PORTFOLIO_LEGACY_RANKING_TITLE");
    expect(helpers).toContain("rankProjectsByQcPressure");
  });
});
