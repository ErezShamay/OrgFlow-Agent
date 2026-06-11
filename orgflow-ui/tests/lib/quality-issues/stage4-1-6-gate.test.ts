import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 4.1.6 gate (portfolio page QC-first UI)", () => {
  it("keeps portfolio page QC-first without blocking on legacy API", () => {
    const page = readSource("app/(dashboard)/portfolio/page.tsx");
    const legacy = readSource(
      "components/quality-issues/PortfolioLegacySection.tsx"
    );
    const helpers = readSource("lib/quality-issues/portfolio-page.ts");

    expect(page).toContain("PortfolioQualitySummaryPanel");
    expect(page).toContain("PortfolioProjectRanking");
    expect(page).toContain("PortfolioLegacySection");
    expect(page).not.toContain("useOrgQuery");
    expect(page).not.toContain("/portfolio/summary");
    expect(legacy).toContain('enabled: expanded');
    expect(legacy).toContain("PORTFOLIO_LEGACY_DEFAULT_EXPANDED");
    expect(helpers).toContain("PORTFOLIO_QC_PAGE_SUBTITLE");
  });

  it("collapses legacy Health Score section by default", () => {
    const legacy = readSource(
      "components/quality-issues/PortfolioLegacySection.tsx"
    );

    expect(legacy).toContain('useState(PORTFOLIO_LEGACY_DEFAULT_EXPANDED)');
    expect(legacy).toContain("aria-expanded={expanded}");
    expect(legacy).toContain("PORTFOLIO_LEGACY_RANKING_TITLE");
  });
});
