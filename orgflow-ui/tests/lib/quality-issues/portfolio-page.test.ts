import { describe, expect, it } from "vitest";

import {
  PORTFOLIO_LEGACY_DEFAULT_EXPANDED,
  PORTFOLIO_QC_PAGE_SUBTITLE,
  PORTFOLIO_QC_PAGE_TITLE,
  portfolioLegacySectionId,
} from "@/lib/quality-issues/portfolio-page";

describe("portfolio page helpers (4.1.6)", () => {
  it("positions QC as the primary portfolio view", () => {
    expect(PORTFOLIO_QC_PAGE_TITLE).toBe("תיק בקרת איכות");
    expect(PORTFOLIO_QC_PAGE_SUBTITLE).toContain("ליקויים");
    expect(PORTFOLIO_QC_PAGE_SUBTITLE).toContain("דירוג פרויקטים");
  });

  it("keeps legacy PM section collapsed by default", () => {
    expect(PORTFOLIO_LEGACY_DEFAULT_EXPANDED).toBe(false);
  });

  it("exposes stable legacy section anchor id", () => {
    expect(portfolioLegacySectionId()).toBe("portfolio-legacy-section");
  });
});
