/**
 * Gate D5 — trade drill-down from supervision dashboard.
 */
import { existsSync, readFileSync } from "node:fs";
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

describe("supervision dashboard D5 gate", () => {
  it("wires trade detail API and page", () => {
    const lib = readUiSource("lib/projects/supervision-dashboard.ts");
    const page = readUiSource("app/(dashboard)/projects/[id]/trades/[tradeKey]/page.tsx");
    const view = readUiSource("components/projects/ProjectTradeDetailView.tsx");
    const mainPy = readRepoSource("app/main.py");
    const aggregation = readRepoSource("app/lib/supervision_dashboard_aggregation.py");

    expect(lib).toContain("fetchProjectSupervisionTradeDetail");
    expect(lib).toContain("/supervision-dashboard/trades/");
    expect(page).toContain("ProjectTradeDetailView");
    expect(view).toContain("fetchProjectSupervisionTradeDetail");
    expect(view).toContain("display_status_he");
    expect(view).toContain("/issues/");
    expect(mainPy).toContain("/supervision-dashboard/trades/{trade_key}");
    expect(aggregation).toContain("aggregate_supervision_trade_detail");
  });

  it("links trade rows from dashboard panel to trade page", () => {
    const panel = readUiSource("components/projects/ProjectTradeProgressPanel.tsx");
    const dashboard = readUiSource("components/projects/ProjectSupervisionDashboard.tsx");

    expect(panel).toContain("projectSupervisionTradePagePath");
    expect(dashboard).toContain("projectId={projectId}");
    expect(
      existsSync(
        path.join(UI_ROOT, "app/(dashboard)/projects/[id]/trades/[tradeKey]/page.tsx")
      )
    ).toBe(true);
  });
});
