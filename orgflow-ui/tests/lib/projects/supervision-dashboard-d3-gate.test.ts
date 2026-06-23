/**
 * Gate D3 — supervision dashboard UI components (KPI + trades + apartments).
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  canViewProjectSupervisionDashboard,
  parseProjectSupervisionDashboard,
} from "@/lib/projects/supervision-dashboard";
import {
  SUPERVISION_OVERALL_STATUS_LABELS,
  supervisionTradeBarColor,
} from "@/lib/projects/supervision-dashboard-types";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("supervision dashboard D3 gate", () => {
  it("defines types, parser, and API fetch for supervision-dashboard", () => {
    const lib = readUiSource("lib/projects/supervision-dashboard.ts");
    const types = readUiSource("lib/projects/supervision-dashboard-types.ts");

    expect(lib).toContain("fetchProjectSupervisionDashboard");
    expect(lib).toContain("/supervision-dashboard");
    expect(lib).toContain("canViewProjectSupervisionDashboard");
    expect(types).toContain("ProjectSupervisionDashboard");
    expect(types).toContain("overall_status");
    expect(types).toContain("parseProjectSupervisionDashboard");
  });

  it("parses API payload into dashboard model", () => {
    const parsed = parseProjectSupervisionDashboard({
      project_id: "proj-1",
      project_name: "מגדלי הים",
      overall_status: "attention",
      kpis: {
        in_treatment: 2,
        with_defects: 5,
        completed: 10,
        total_items: 17,
        progress_percent: 59,
      },
      trades: [
        {
          trade_key: "electrical",
          label_he: "חשמל",
          total_items: 4,
          completed: 3,
          with_defects: 1,
          in_treatment: 0,
          progress_percent: 75,
        },
      ],
      apartments: [
        {
          apartment_id: "apt-1",
          apartment_number: "6",
          group_key: "apartment:6",
          total_items: 3,
          completed: 2,
          with_defects: 1,
          in_treatment: 0,
          open_issues_count: 2,
          progress_percent: 67,
          last_visit_report_id: "visit-1",
          last_visit_at: "2026-06-20T10:00:00Z",
        },
      ],
      public_areas: [],
    });

    expect(parsed.project_name).toBe("מגדלי הים");
    expect(parsed.kpis.progress_percent).toBe(59);
    expect(parsed.trades[0]?.label_he).toBe("חשמל");
    expect(parsed.apartments[0]?.apartment_number).toBe("6");
  });

  it("wires ProVisor-style dashboard components with Hebrew RTL labels", () => {
    const dashboard = readUiSource(
      "components/projects/ProjectSupervisionDashboard.tsx"
    );
    const kpiRow = readUiSource(
      "components/projects/ProjectSupervisionKpiRow.tsx"
    );
    const trades = readUiSource(
      "components/projects/ProjectTradeProgressPanel.tsx"
    );
    const apartments = readUiSource(
      "components/projects/ProjectApartmentProgressGrid.tsx"
    );

    expect(existsSync(path.join(UI_ROOT, "components/projects/ProjectSupervisionDashboard.tsx"))).toBe(true);
    expect(existsSync(path.join(UI_ROOT, "components/projects/ProjectSupervisionKpiRow.tsx"))).toBe(true);
    expect(existsSync(path.join(UI_ROOT, "components/projects/ProjectTradeProgressPanel.tsx"))).toBe(true);
    expect(existsSync(path.join(UI_ROOT, "components/projects/ProjectApartmentProgressGrid.tsx"))).toBe(true);

    expect(dashboard).toContain("fetchProjectSupervisionDashboard");
    expect(dashboard).toContain('dir="rtl"');
    expect(dashboard).toContain("LoadingState");
    expect(dashboard).toContain("error.message");

    expect(kpiRow).toContain("בטיפול");
    expect(kpiRow).toContain("עם ליקויים");
    expect(kpiRow).toContain("הושלמו");
    expect(kpiRow).toContain("התקדמות כללית");
    expect(kpiRow).toContain("מתוך");

    expect(trades).toContain("התקדמות לפי קטגוריה");
    expect(trades).toContain("progress_percent");
    expect(trades).toContain("supervisionTradeBarColor");

    expect(apartments).toContain("התקדמות לפי דירה");
    expect(apartments).toContain("תיעוד ביקור");
    expect(apartments).toContain("ליקויים");
    expect(apartments).toContain("projectApartmentPortalPath");
  });

  it("maps overall status labels and trade bar colors", () => {
    expect(SUPERVISION_OVERALL_STATUS_LABELS.healthy).toBe("תקין");
    expect(SUPERVISION_OVERALL_STATUS_LABELS.attention).toBe("דורש טיפול");
    expect(SUPERVISION_OVERALL_STATUS_LABELS.critical).toBe("קריטי");
    expect(supervisionTradeBarColor(0)).toMatch(/^bg-/);
    expect(canViewProjectSupervisionDashboard("SUPERVISOR")).toBe(true);
    expect(canViewProjectSupervisionDashboard("CONTRACTOR")).toBe(false);
  });
});
