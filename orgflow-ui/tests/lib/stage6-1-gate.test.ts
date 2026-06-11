import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(root: string, relativePath: string): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

describe("stage 6.1 gate (trade heatmap)", () => {
  it("wires portfolio trade heatmap API and panel", () => {
    const portfolioPage = readSource(
      UI_ROOT,
      "app/(dashboard)/portfolio/page.tsx"
    );
    const panel = readSource(
      UI_ROOT,
      "components/quality-issues/PortfolioTradeHeatmapPanel.tsx"
    );
    const api = readSource(UI_ROOT, "lib/quality-issues/api.ts");
    const mainPy = readSource(REPO_ROOT, "app/main.py");
    const servicePy = readSource(
      REPO_ROOT,
      "app/services/quality_issue_trade_heatmap.py"
    );

    expect(portfolioPage).toContain("PortfolioTradeHeatmapPanel");
    expect(panel).toContain("getPortfolioTradeHeatmap");
    expect(panel).toContain("מפת חום לפי מלאכה");
    expect(api).toContain("/portfolio/quality-trade-heatmap");
    expect(mainPy).toContain("/portfolio/quality-trade-heatmap");
    expect(servicePy).toContain("build_trade_heatmap_cells");
  });
});
