import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(root: string, relativePath: string): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

describe("stage 6.2 gate (recurring rankings)", () => {
  it("wires portfolio recurring rankings API and panel", () => {
    const portfolioPage = readSource(
      UI_ROOT,
      "app/(dashboard)/portfolio/page.tsx"
    );
    const panel = readSource(
      UI_ROOT,
      "components/quality-issues/PortfolioRecurringRankingsPanel.tsx"
    );
    const api = readSource(UI_ROOT, "lib/quality-issues/api.ts");
    const mainPy = readSource(REPO_ROOT, "app/main.py");
    const servicePy = readSource(
      REPO_ROOT,
      "app/services/quality_issue_recurring_rankings.py"
    );

    expect(portfolioPage).toContain("PortfolioRecurringRankingsPanel");
    expect(panel).toContain("getPortfolioRecurringRankings");
    expect(panel).toContain("ליקויים חוזרים וקבלני משנה");
    expect(api).toContain("/portfolio/quality-recurring-rankings");
    expect(mainPy).toContain("/portfolio/quality-recurring-rankings");
    expect(servicePy).toContain("build_contractor_recurring_rankings");
    expect(servicePy).toContain("build_recurring_issue_rankings");
  });
});
