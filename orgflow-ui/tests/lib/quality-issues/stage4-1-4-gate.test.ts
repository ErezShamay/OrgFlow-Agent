import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(relativePath: string, root = UI_ROOT): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

describe("stage 4.1.4 gate (average open days KPI)", () => {
  it("ships backend average-open-days helpers and service wiring", () => {
    const kpiModule = readSource(
      "app/services/quality_issue_portfolio_kpi.py",
      REPO_ROOT
    );
    const service = readSource(
      "app/services/quality_issue_service.py",
      REPO_ROOT
    );

    expect(kpiModule).toContain("compute_average_open_days");
    expect(kpiModule).toContain("aggregate_average_open_days_by_project");
    expect(kpiModule).toContain("AVERAGE_OPEN_DAYS_HEALTHY_THRESHOLD = 14");
    expect(service).toContain("compute_average_open_days");
    expect(service).toContain("average_open_days_by_project");
  });

  it("shows average open days KPI in portfolio QC panel", () => {
    const panel = readSource(
      "components/quality-issues/PortfolioQualitySummaryPanel.tsx"
    );
    const helpers = readSource("lib/quality-issues/portfolio-summary.ts");

    expect(panel).toContain("ממוצע ימים פתוח");
    expect(panel).toContain("average_open_days");
    expect(panel).toContain("formatAverageOpenDaysCaption");
    expect(helpers).toContain("formatAverageOpenDaysCaption");
    expect(helpers).toContain("isAverageOpenDaysHealthy");
  });
});
