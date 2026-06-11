import { describe, expect, it } from "vitest";

import {
  countProjectsWithOpenIssues,
  formatOpenIssuesPerProjectCaption,
  openIssuesPerProjectRows,
  rankProjectsByQcPressure,
} from "@/lib/quality-issues/portfolio-summary";
import type { QualityPortfolioProjectSummary } from "@/lib/quality-issues/types";

const SAMPLE_PROJECTS: QualityPortfolioProjectSummary[] = [
  {
    project_id: "proj-1",
    project_name: "א",
    open_total: 2,
    open_critical: 1,
    critical_open_over_14_days: 0,
    average_open_days: 7,
  },
  {
    project_id: "proj-2",
    project_name: "ב",
    open_total: 0,
    open_critical: 0,
    critical_open_over_14_days: 0,
    average_open_days: null,
  },
  {
    project_id: "proj-3",
    project_name: "ג",
    open_total: 1,
    open_critical: 0,
    critical_open_over_14_days: 0,
    average_open_days: 3,
  },
];

describe("portfolio open issues per project (4.1.1)", () => {
  it("counts projects with open issues", () => {
    expect(countProjectsWithOpenIssues(SAMPLE_PROJECTS)).toBe(2);
  });

  it("formats caption for portfolio header", () => {
    expect(formatOpenIssuesPerProjectCaption(SAMPLE_PROJECTS)).toBe(
      "2 פרויקטים עם ליקויים פתוחים מתוך 3"
    );
  });

  it("preserves all project rows for per-project KPI table", () => {
    expect(openIssuesPerProjectRows(SAMPLE_PROJECTS)).toHaveLength(3);
  });

  it("sorts by open critical then open total", () => {
    expect(rankProjectsByQcPressure(SAMPLE_PROJECTS).map((p) => p.project_id)).toEqual(
      ["proj-1", "proj-3", "proj-2"]
    );
  });
});
