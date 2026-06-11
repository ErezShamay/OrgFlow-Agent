import { describe, expect, it } from "vitest";

import {
  CLOSED_WITHIN_DAYS_HEALTHY_PERCENT,
  CLOSED_WITHIN_DAYS_THRESHOLD,
  formatClosedWithin30DaysCaption,
  formatClosedWithin30DaysPercent,
  isClosedWithin30DaysHealthy,
} from "@/lib/quality-issues/portfolio-summary";

describe("portfolio closed within 30 days KPI (4.1.3)", () => {
  it("uses 30-day threshold constant", () => {
    expect(CLOSED_WITHIN_DAYS_THRESHOLD).toBe(30);
  });

  it("formats percent value", () => {
    expect(formatClosedWithin30DaysPercent(75.5)).toBe("75.5%");
    expect(formatClosedWithin30DaysPercent(null)).toBe("-");
  });

  it("formats caption when closed issues exist", () => {
    expect(
      formatClosedWithin30DaysCaption({ closed_within_30_days_percent: 80 })
    ).toBe("80% מהליקויים הסגורים נסגרו תוך 30 יום");
  });

  it("formats caption when no closed issues", () => {
    expect(
      formatClosedWithin30DaysCaption({ closed_within_30_days_percent: null })
    ).toBe("אין ליקויים סגורים לחישוב אחוז סגירה");
  });

  it("detects healthy closure rate", () => {
    expect(isClosedWithin30DaysHealthy(80)).toBe(true);
    expect(isClosedWithin30DaysHealthy(79.9)).toBe(false);
    expect(isClosedWithin30DaysHealthy(null)).toBe(false);
    expect(CLOSED_WITHIN_DAYS_HEALTHY_PERCENT).toBe(80);
  });
});
