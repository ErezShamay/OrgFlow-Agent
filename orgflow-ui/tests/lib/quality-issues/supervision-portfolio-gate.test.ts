/**
 * Gate F→G — Portfolio + project field-first (P4 §6, §11.3).
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

describe("supervision portfolio gate (P4 + §11.3)", () => {
  it("filters portfolio KPI aggregations to published issues only", () => {
    const kpiModule = readRepoSource("app/services/quality_issue_portfolio_kpi.py");
    const service = readRepoSource("app/services/quality_issue_service.py");

    expect(kpiModule).toContain("filter_published_portfolio_issues");
    expect(kpiModule).toContain("is_published_portfolio_issue");
    expect(kpiModule).toContain("IssueVisibility.PUBLISHED.value");
    expect(kpiModule).toContain("resolve_latest_published_report_at");
    expect(kpiModule).toContain(
      "rank_portfolio_projects_by_supervision_pressure"
    );
    expect(service).toContain("filter_published_portfolio_issues");
    expect(service).toContain("resolve_latest_published_report_at");
    expect(service).toContain("last_report_at=last_report_at");
  });

  it("shows supervision portfolio KPIs without health or AI", () => {
    const portfolioPage = readUiSource("app/(dashboard)/portfolio/page.tsx");
    const panel = readUiSource(
      "components/quality-issues/PortfolioQualitySummaryPanel.tsx"
    );
    const ranking = readUiSource(
      "components/quality-issues/PortfolioProjectRanking.tsx"
    );
    const copy = readUiSource("lib/quality-issues/portfolio-page.ts");

    expect(copy).toContain("תיק פיקוח הנדסי");
    expect(portfolioPage).toContain("PortfolioQualitySummaryPanel");
    expect(portfolioPage).toContain("/portfolio/deliverables");
    expect(portfolioPage).not.toMatch(/health score/i);
    expect(portfolioPage).not.toContain("ProjectInsightsPanel");
    expect(panel).toContain("ליקויים פתוחים");
    expect(panel).toContain("קריטיים פתוחים");
    expect(panel).toContain("דוח אחרון");
    expect(panel).toContain("formatLastReportAtKpi");
    expect(panel).not.toMatch(/AI/i);
    expect(ranking).toContain("rankProjectsBySupervisionPressure");
    expect(ranking).not.toMatch(/\bQC\b/);
  });

  it("refactors project overview to field-first supervision", () => {
    const projectPage = readUiSource("app/(dashboard)/projects/[id]/page.tsx");
    const settingsPage = readUiSource(
      "app/(dashboard)/projects/[id]/settings/page.tsx"
    );
    const dashboard = readUiSource(
      "components/projects/ProjectSupervisionDashboard.tsx"
    );
    const nav = readUiSource("lib/qc-navigation.ts");

    expect(projectPage).toContain("ProjectSupervisionDashboard");
    expect(projectPage).toContain("ProjectVisitIssueDiffSummary");
    expect(projectPage).toContain("isVisibleToResident");
    expect(dashboard).toContain("דשבורד פיקוח הנדסי");
    expect(dashboard).toContain("ProjectFieldReportLink");
    expect(dashboard).toContain("כל הליקויים");
    expect(settingsPage).toContain("ProjectDetailsEditor");
    expect(settingsPage).toContain("ProjectDocumentsArchive");
    expect(settingsPage).toContain("ProjectActivityTimeline");
    expect(projectPage).not.toContain("ProjectInsightsPanel");
    expect(projectPage).not.toContain("health.score");
    expect(projectPage).not.toContain("operationalSummary");
    expect(projectPage).not.toContain("AI_REVIEWS_KPI_LABEL");
    expect(projectPage).not.toMatch(/ביקורות AI/i);
    expect(projectPage).not.toContain("פעולות פתוחות");
    expect(projectPage).not.toContain("נקודות סיכון");
    expect(nav).toContain('label: "סקירה"');
    expect(nav).toContain('label: "ליקויים"');
    expect(nav).toContain('label: "דיירים"');
    expect(nav).toContain("buildSupervisionProjectNavItems");
    expect(nav).toContain("getSupervisionProjectSecondaryNavLinks");
    expect(nav).not.toContain('id: "reviews_ai"');
  });
});
