import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(relativePath: string, root = UI_ROOT): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

describe("stage 4.1.3 gate (closed within 30 days KPI)", () => {
  it("ships backend closed-within-30 helpers and service wiring", () => {
    const kpiModule = readSource(
      "app/services/quality_issue_portfolio_kpi.py",
      REPO_ROOT
    );
    const service = readSource(
      "app/services/quality_issue_service.py",
      REPO_ROOT
    );

    expect(kpiModule).toContain("compute_closed_within_days_percent");
    expect(kpiModule).toContain("CLOSED_WITHIN_DAYS_THRESHOLD = 30");
    expect(service).toContain("compute_closed_within_days_percent");
    expect(service).toContain("closed_within_30_days_percent");
  });

  it("shows closed-within-30 KPI in portfolio QC panel", () => {
    const panel = readSource(
      "components/quality-issues/PortfolioQualitySummaryPanel.tsx"
    );
    const helpers = readSource("lib/quality-issues/portfolio-summary.ts");

    expect(panel).toContain("סגירה תוך 30 יום");
    expect(panel).toContain("closed_within_30_days_percent");
    expect(panel).toContain("formatClosedWithin30DaysCaption");
    expect(helpers).toContain("formatClosedWithin30DaysCaption");
    expect(helpers).toContain("isClosedWithin30DaysHealthy");
  });
});
