import { describe, expect, it } from "vitest";

import {
  AVERAGE_OPEN_DAYS_HEALTHY_THRESHOLD,
  formatAverageOpenDays,
  formatAverageOpenDaysCaption,
  isAverageOpenDaysHealthy,
} from "@/lib/quality-issues/portfolio-summary";

describe("portfolio average open days KPI (4.1.4)", () => {
  it("uses 14-day healthy threshold constant", () => {
    expect(AVERAGE_OPEN_DAYS_HEALTHY_THRESHOLD).toBe(14);
  });

  it("formats average open days value", () => {
    expect(formatAverageOpenDays(7.5)).toBe("7.5 ימים");
    expect(formatAverageOpenDays(null)).toBe("-");
  });

  it("formats caption when open issues exist", () => {
    expect(
      formatAverageOpenDaysCaption({
        average_open_days: 10,
        total_open: 3,
      })
    ).toBe("ממוצע 10 ימים פתוח לליקוי (3 פתוחים)");
  });

  it("formats caption when no open issues", () => {
    expect(
      formatAverageOpenDaysCaption({
        average_open_days: null,
        total_open: 0,
      })
    ).toBe("אין ליקויים פתוחים לחישוב ממוצע ימים");
  });

  it("detects healthy average open days", () => {
    expect(isAverageOpenDaysHealthy(14)).toBe(true);
    expect(isAverageOpenDaysHealthy(14.1)).toBe(false);
    expect(isAverageOpenDaysHealthy(null)).toBe(false);
  });
});
