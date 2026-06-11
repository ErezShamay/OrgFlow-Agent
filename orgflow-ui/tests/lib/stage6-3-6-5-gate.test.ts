import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(root: string, relativePath: string): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

describe("stage 6.3 gate (periodic report)", () => {
  it("wires periodic report API and export panel", () => {
    const portfolioPage = readSource(
      UI_ROOT,
      "app/(dashboard)/portfolio/page.tsx"
    );
    const panel = readSource(
      UI_ROOT,
      "components/quality-issues/PortfolioPeriodicReportExport.tsx"
    );
    const api = readSource(UI_ROOT, "lib/quality-issues/api.ts");
    const mainPy = readSource(REPO_ROOT, "app/main.py");
    const servicePy = readSource(
      REPO_ROOT,
      "app/services/quality_issue_periodic_report_service.py"
    );

    expect(portfolioPage).toContain("PortfolioPeriodicReportExport");
    expect(panel).toContain("getPortfolioPeriodicReport");
    expect(panel).toContain("ייצוא Excel (CSV)");
    expect(panel).toContain("ייצוא PDF");
    expect(api).toContain("/portfolio/quality-periodic-report");
    expect(mainPy).toContain("/portfolio/quality-periodic-report/export");
    expect(servicePy).toContain("render_periodic_report_csv");
  });
});

describe("stage 6.4 gate (catalog supplement)", () => {
  it("merges catalog supplement at load time", () => {
    const parser = readSource(
      REPO_ROOT,
      "app/services/field_report_catalog_parser.py"
    );
    const supplement = readSource(
      REPO_ROOT,
      "app/config/field_report_catalog_supplement.py"
    );

    expect(parser).toContain("merge_catalog_supplement");
    expect(parser).toContain("SUPPLEMENT_ISSUES");
    expect(supplement).toContain("QC-STR-001");
    expect(supplement).toContain("QC-FIN-001");
  });
});

describe("stage 6.5 gate (catalog standard_ref link)", () => {
  it("wires catalog link resolver and issue detail UI", () => {
    const resolver = readSource(
      REPO_ROOT,
      "app/services/catalog_standard_ref_resolver.py"
    );
    const servicePy = readSource(
      REPO_ROOT,
      "app/services/quality_issue_service.py"
    );
    const issueDetail = readSource(
      UI_ROOT,
      "lib/quality-issues/issue-detail.ts"
    );
    const panel = readSource(
      UI_ROOT,
      "components/quality-issues/IssueDetailPanel.tsx"
    );

    expect(resolver).toContain("resolve_catalog_link_for_issue");
    expect(servicePy).toContain("catalog_link");
    expect(issueDetail).toContain("formatCatalogSectionLabel");
    expect(panel).toContain("catalogLink");
  });
});
