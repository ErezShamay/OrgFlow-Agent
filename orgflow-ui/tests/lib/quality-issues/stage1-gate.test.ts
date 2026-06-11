import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  buildIssueTableRow,
  issueHasPhotos,
} from "@/components/quality-issues/IssuesTable";
import {
  formatAverageOpenDays,
  rankProjectsByQcPressure,
} from "@/lib/quality-issues/portfolio-summary";
import { parseQualityIssueListResponse } from "@/lib/quality-issues/types";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

const NOW = "2026-06-09T12:00:00.000Z";

describe("stage 1 gate (Issue Registry)", () => {
  it("maps materialized issue photos into the issues table", () => {
    const parsed = parseQualityIssueListResponse({
      project_id: "proj-1",
      total: 5,
      limit: 50,
      offset: 0,
      items: Array.from({ length: 5 }, (_item, index) => ({
        id: `issue-${index + 1}`,
        organization_id: "org-1",
        project_id: "proj-1",
        title: `ליקוי ${index + 1}`,
        severity: index === 0 ? "CRITICAL" : "MEDIUM",
        status: "OPEN",
        first_seen_report_id: "report-gate",
        first_seen_at: NOW,
        last_seen_report_id: "report-gate",
        last_seen_at: NOW,
        materialization_key: `report-gate:row-${index + 1}`,
        photo_ids: [`photo-${index + 1}`],
        recurrence_count: 0,
      })),
    });

    expect(parsed.total).toBe(5);
    expect(parsed.items.every((issue) => issue.photo_ids.length === 1)).toBe(true);

    const row = buildIssueTableRow(parsed.items[0]!, { projectId: "proj-1" });
    expect(issueHasPhotos(parsed.items[0]!.photo_ids)).toBe(true);
    expect(row.hasPhotos).toBe(true);
    expect(row.photoCount).toBe(1);
    expect(row.photoCountLabel).toBe("1 תמונות");
  });

  it("formats portfolio QC KPI helpers", () => {
    expect(formatAverageOpenDays(7)).toBe("7 ימים");
    expect(formatAverageOpenDays(null)).toBe("-");

    const ranked = rankProjectsByQcPressure([
      {
        project_id: "proj-1",
        project_name: "א",
        open_total: 3,
        open_critical: 1,
        critical_open_over_14_days: 0,
      },
      {
        project_id: "proj-2",
        project_name: "ב",
        open_total: 5,
        open_critical: 2,
        critical_open_over_14_days: 0,
      },
    ]);

    expect(ranked[0]?.project_id).toBe("proj-2");
  });
});

describe("stage 1 gate UI wiring", () => {
  it("connects issues table photos and portfolio QC summary panel", () => {
    const issuesTable = readUiSource("components/quality-issues/IssuesTable.tsx");
    const portfolioPanel = readUiSource(
      "components/quality-issues/PortfolioQualitySummaryPanel.tsx"
    );
    const portfolioPage = readUiSource("app/(dashboard)/portfolio/page.tsx");
    const portfolioHelpers = readUiSource(
      "lib/quality-issues/portfolio-summary.ts"
    );

    expect(issuesTable).toContain("issueHasPhotos");
    expect(issuesTable).toContain("תמונות מדוח השטח");
    expect(portfolioPanel).toContain("getPortfolioQualitySummary");
    expect(portfolioPanel).toContain("ליקויים פתוחים");
    expect(portfolioPanel).toContain("קריטיים פתוחים");
    expect(portfolioPanel).toContain("ממוצע ימים פתוח");
    expect(portfolioPage).toContain("PortfolioQualitySummaryPanel");
    expect(portfolioPage).toContain("PortfolioProjectRanking");
    expect(portfolioPage).toContain("PortfolioLegacySection");
    expect(portfolioPage).toContain("PORTFOLIO_QC_PAGE_EYEBROW");
    expect(portfolioHelpers).toContain("rankProjectsByQcPressure");
  });
});
