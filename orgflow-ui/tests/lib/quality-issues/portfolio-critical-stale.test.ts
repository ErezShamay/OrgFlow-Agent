import { describe, expect, it } from "vitest";

import {
  CRITICAL_STALE_DAYS_THRESHOLD,
  countProjectsWithStaleCriticalIssues,
  formatCriticalOpenOver14DaysCaption,
  rankProjectsByQcPressure,
} from "@/lib/quality-issues/portfolio-summary";
import type { QualityPortfolioProjectSummary } from "@/lib/quality-issues/types";

const SAMPLE_PROJECTS: QualityPortfolioProjectSummary[] = [
  {
    project_id: "proj-1",
    project_name: "א",
    open_total: 2,
    open_critical: 2,
    critical_open_over_14_days: 1,
    average_open_days: 15,
  },
  {
    project_id: "proj-2",
    project_name: "ב",
    open_total: 1,
    open_critical: 1,
    critical_open_over_14_days: 0,
    average_open_days: 4,
  },
  {
    project_id: "proj-3",
    project_name: "ג",
    open_total: 1,
    open_critical: 0,
    critical_open_over_14_days: 0,
  },
];

describe("portfolio critical stale KPI (4.1.2)", () => {
  it("uses 14-day threshold constant", () => {
    expect(CRITICAL_STALE_DAYS_THRESHOLD).toBe(14);
  });

  it("formats caption when stale critical issues exist", () => {
    expect(
      formatCriticalOpenOver14DaysCaption({
        critical_open_over_14_days: 2,
        total_open_critical: 3,
      })
    ).toBe("2 ליקויים קריטיים פתוחים מעל 14 יום");
  });

  it("formats caption when no stale critical issues", () => {
    expect(
      formatCriticalOpenOver14DaysCaption({
        critical_open_over_14_days: 0,
        total_open_critical: 1,
      })
    ).toBe("אין ליקויים קריטיים פתוחים מעל 14 יום");
  });

  it("counts projects with stale critical issues", () => {
    expect(countProjectsWithStaleCriticalIssues(SAMPLE_PROJECTS)).toBe(1);
  });

  it("ranks projects by open critical then open total", () => {
    expect(rankProjectsByQcPressure(SAMPLE_PROJECTS).map((p) => p.project_id)).toEqual(
      ["proj-1", "proj-2", "proj-3"]
    );
  });
});
