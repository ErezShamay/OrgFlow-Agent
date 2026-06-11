import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(relativePath: string, root = UI_ROOT): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

describe("stage 4.1.2 gate (critical open > 14 days KPI)", () => {
  it("ships backend stale-critical KPI helpers and service wiring", () => {
    const kpiModule = readSource(
      "app/services/quality_issue_portfolio_kpi.py",
      REPO_ROOT
    );
    const service = readSource(
      "app/services/quality_issue_service.py",
      REPO_ROOT
    );

    expect(kpiModule).toContain("count_critical_open_over_days");
    expect(kpiModule).toContain("aggregate_critical_stale_by_project");
    expect(kpiModule).toContain("CRITICAL_STALE_DAYS_THRESHOLD = 14");
    expect(service).toContain("count_critical_open_over_days");
    expect(service).toContain("critical_open_over_14_days");
  });

  it("shows stale critical KPI in portfolio QC panel", () => {
    const panel = readSource(
      "components/quality-issues/PortfolioQualitySummaryPanel.tsx"
    );
    const helpers = readSource("lib/quality-issues/portfolio-summary.ts");

    expect(panel).toContain("קריטיים > 14 יום");
    expect(panel).toContain("critical_open_over_14_days");
    expect(panel).toContain("formatCriticalOpenOver14DaysCaption");
    expect(helpers).toContain("formatCriticalOpenOver14DaysCaption");
    expect(helpers).toContain("countProjectsWithStaleCriticalIssues");
  });
});
