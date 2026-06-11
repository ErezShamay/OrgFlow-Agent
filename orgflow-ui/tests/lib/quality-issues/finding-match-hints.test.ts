import { describe, expect, it } from "vitest";

import {
  buildSuggestMatchesRequestFromFindingRow,
  formatSimilarIssueSummary,
  hasMatchableFindingFields,
} from "@/lib/quality-issues/finding-match-hints";

describe("finding match hints (2.1.4)", () => {
  it("requires at least one of location, trade, or group_key", () => {
    expect(hasMatchableFindingFields({})).toBe(false);
    expect(hasMatchableFindingFields({ location: "  " })).toBe(false);
    expect(hasMatchableFindingFields({ trade: "אינסטלציה" })).toBe(true);
    expect(
      hasMatchableFindingFields({
        location: "דירה 3",
        group_key: "bath",
      })
    ).toBe(true);
  });

  it("builds suggest-matches request from finding row fields", () => {
    expect(
      buildSuggestMatchesRequestFromFindingRow({
        location: " דירה 3 ",
        trade: "אינסטלציה",
        group_key: "bath",
        issue_id: "STR-001",
      })
    ).toEqual({
      location: "דירה 3",
      trade: "אינסטלציה",
      group_key: "bath",
      catalog_issue_id: "STR-001",
    });
  });

  it("formats similar issue summary for display", () => {
    expect(
      formatSimilarIssueSummary({
        title: "נזילה",
        location: "דירה 3",
        trade: "אינסטלציה",
      })
    ).toBe("נזילה - דירה 3 · אינסטלציה");
  });
});
