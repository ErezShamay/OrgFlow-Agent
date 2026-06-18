/**
 * Gate R1 — live portfolio SSE / polling wiring (COMPETITIVE-LAYER-TASKS.md).
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  PORTFOLIO_LIVE_POLL_INTERVAL_MS,
  buildPortfolioEventsPath,
  buildPortfolioLiveSnapshotPath,
  parsePortfolioLiveSnapshot,
  parseSseDataLines,
} from "@/lib/quality-issues/portfolio-live";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

function readBackendSource(relativePath: string): string {
  return readFileSync(path.join(REPO_ROOT, relativePath), "utf8");
}

describe("portfolio live gate R1", () => {
  it("backend exposes SSE + polling snapshot routes", () => {
    const main = readBackendSource("app/main.py");
    const service = readBackendSource("app/services/portfolio_live_service.py");

    expect(main).toContain("/portfolio/events");
    expect(main).toContain("/portfolio/live-snapshot");
    expect(main).toContain("get_portfolio_live_snapshot");
    expect(service).toContain("PORTFOLIO_LIVE_INTERVAL_SECONDS = 30");
    expect(service).toContain("portfolio.snapshot");
  });

  it("portfolio page wires live counter updates", () => {
    const panel = readUiSource(
      "components/quality-issues/PortfolioQualitySummaryPanel.tsx"
    );
    const hook = readUiSource("hooks/usePortfolioLiveUpdates.ts");
    const live = readUiSource("lib/quality-issues/portfolio-live.ts");

    expect(existsSync(path.join(UI_ROOT, "hooks/usePortfolioLiveUpdates.ts"))).toBe(
      true
    );
    expect(panel).toContain("usePortfolioLiveUpdates");
    expect(panel).toContain("ליקויים פתוחים");
    expect(hook).toContain("connectPortfolioLiveUpdates");
    expect(live).toContain("PORTFOLIO_LIVE_POLL_INTERVAL_MS = 30_000");
  });

  it("parses live snapshot + SSE chunks", () => {
    expect(buildPortfolioEventsPath()).toBe("/portfolio/events");
    expect(buildPortfolioLiveSnapshotPath()).toBe("/portfolio/live-snapshot");
    expect(PORTFOLIO_LIVE_POLL_INTERVAL_MS).toBe(30_000);

    const snapshot = parsePortfolioLiveSnapshot({
      organization_id: "org-1",
      total_open: 4,
      total_open_critical: 1,
      updated_at: "2026-06-18T12:00:00+00:00",
    });

    expect(snapshot.total_open).toBe(4);
    expect(snapshot.total_open_critical).toBe(1);

    const parsed = parseSseDataLines(
      'event: portfolio.snapshot\ndata: {"total_open":2}\n\n'
    );

    expect(parsed.events).toEqual(['{"total_open":2}']);
    expect(parsed.remainder).toBe("");
  });
});
