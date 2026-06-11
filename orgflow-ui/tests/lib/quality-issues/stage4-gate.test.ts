import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  countProjectsWithOpenCritical,
  projectQcPressureLevel,
  rankProjectsByQcPressure,
} from "@/lib/quality-issues/portfolio-summary";
import { hasQCPermission } from "@/lib/quality-issues/permissions";
import { recommendedPostLoginRoute } from "@/lib/qc-navigation";
import type { QualityPortfolioProjectSummary } from "@/lib/quality-issues/types";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(relativePath: string, root = UI_ROOT): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

const CRITICAL_PORTFOLIO: QualityPortfolioProjectSummary[] = [
  {
    project_id: "proj-safe",
    project_name: "פרויקט ירוק",
    open_total: 0,
    open_critical: 0,
    critical_open_over_14_days: 0,
    average_open_days: null,
  },
  {
    project_id: "proj-hot",
    project_name: "האורנים 7",
    open_total: 4,
    open_critical: 2,
    critical_open_over_14_days: 1,
    average_open_days: 12,
  },
];

describe("stage 4 gate (QC portfolio + contractor remediation)", () => {
  it("developer can read QC portfolio and sees critical projects first", () => {
    expect(hasQCPermission("DEVELOPER", "quality_portfolio:read")).toBe(true);
    expect(recommendedPostLoginRoute("DEVELOPER")).toBe("/portfolio");

    const ranked = rankProjectsByQcPressure(CRITICAL_PORTFOLIO);
    expect(ranked[0]?.project_id).toBe("proj-hot");
    expect(countProjectsWithOpenCritical(ranked)).toBe(1);
    expect(projectQcPressureLevel(ranked[0]!)).toBe("critical");
    expect(projectQcPressureLevel(ranked[1]!)).toBe("clear");
  });

  it("portfolio ranking UI highlights critical projects in red", () => {
    const ranking = readSource(
      "components/quality-issues/PortfolioProjectRanking.tsx"
    );
    const portfolioPage = readSource("app/(dashboard)/portfolio/page.tsx");

    expect(portfolioPage).toContain("PortfolioProjectRanking");
    expect(portfolioPage).toContain("PortfolioQualitySummaryPanel");
    expect(ranking).toContain("projectQcPressureLevel");
    expect(ranking).toContain('pressure === "critical"');
    expect(ranking).toContain("border-red-200");
    expect(ranking).toContain("bg-red-100");
    expect(ranking).toContain("open_critical");
  });

  it("contractor remediation photo flow is wired for supervisor verification", () => {
    const statusActions = readSource(
      "components/quality-issues/IssueStatusActions.tsx"
    );
    const statusHelpers = readSource(
      "lib/quality-issues/issue-status-actions.ts"
    );
    const uploadComponent = readSource(
      "components/quality-issues/RemediationPhotoUpload.tsx"
    );
    const verifyActions = readSource(
      "lib/quality-issues/finding-line-issue-actions.ts"
    );
    const lifecycle = readSource(
      "tests/test_qc_stage4_gate.py",
      REPO_ROOT
    );

    expect(statusActions).toContain("RemediationPhotoUpload");
    expect(statusActions).toContain("buildRemediationUpdateRequest");
    expect(statusHelpers).toContain("PENDING_VERIFICATION");
    expect(uploadComponent).toContain("uploadRemediationPhoto");
    expect(verifyActions).toContain("אשר סגירה");
    expect(lifecycle).toContain(
      "test_stage4_gate_contractor_photo_supervisor_approves_on_visit_two"
    );
  });
});
