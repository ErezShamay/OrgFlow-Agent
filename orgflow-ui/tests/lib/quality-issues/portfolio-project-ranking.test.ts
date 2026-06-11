import { describe, expect, it } from "vitest";

import {
  countProjectsWithOpenCritical,
  formatProjectQcRankCaption,
  projectQcPressureLevel,
  rankProjectsByQcPressure,
} from "@/lib/quality-issues/portfolio-summary";
import type { QualityPortfolioProjectSummary } from "@/lib/quality-issues/types";

const SAMPLE_PROJECTS: QualityPortfolioProjectSummary[] = [
  {
    project_id: "proj-1",
    project_name: "א",
    open_total: 3,
    open_critical: 1,
    critical_open_over_14_days: 0,
    average_open_days: 7,
  },
  {
    project_id: "proj-2",
    project_name: "ב",
    open_total: 5,
    open_critical: 2,
    critical_open_over_14_days: 1,
    average_open_days: 15,
  },
  {
    project_id: "proj-3",
    project_name: "ג",
    open_total: 0,
    open_critical: 0,
    critical_open_over_14_days: 0,
    average_open_days: null,
  },
];

describe("portfolio project QC ranking (4.1.5)", () => {
  it("ranks projects by open_critical then open_total", () => {
    expect(rankProjectsByQcPressure(SAMPLE_PROJECTS).map((p) => p.project_id)).toEqual(
      ["proj-2", "proj-1", "proj-3"]
    );
  });

  it("formats ranking caption", () => {
    expect(formatProjectQcRankCaption(SAMPLE_PROJECTS)).toBe(
      "2 פרויקטים עם ליקויים קריטיים, 2 עם ליקויים פתוחים - מתוך 3"
    );
  });

  it("counts projects with open critical issues", () => {
    expect(countProjectsWithOpenCritical(SAMPLE_PROJECTS)).toBe(2);
  });

  it("detects project QC pressure level", () => {
    expect(projectQcPressureLevel(SAMPLE_PROJECTS[1]!)).toBe("critical");
    expect(projectQcPressureLevel(SAMPLE_PROJECTS[0]!)).toBe("critical");
    expect(projectQcPressureLevel(SAMPLE_PROJECTS[2]!)).toBe("clear");
  });
});
