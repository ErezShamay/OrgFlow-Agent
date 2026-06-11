import { describe, expect, it } from "vitest";

import {
  formatTradeHeatmapCaption,
  maxTradeHeatmapSeverityCount,
  tradeHeatmapCellBackground,
  tradeHeatmapIntensity,
} from "@/lib/quality-issues/trade-heatmap";
import { parseQualityTradeHeatmapResponse } from "@/lib/quality-issues/types";

describe("trade heatmap helpers", () => {
  it("parses API response and computes intensity", () => {
    const response = parseQualityTradeHeatmapResponse({
      organization_id: "org-1",
      project_id: null,
      total_open: 3,
      cells: [
        {
          trade: "אינסטלציה",
          open_total: 2,
          open_critical: 1,
          open_high: 1,
          open_medium: 0,
          open_low: 0,
        },
      ],
    });

    expect(response.cells[0]?.trade).toBe("אינסטלציה");
    expect(maxTradeHeatmapSeverityCount(response.cells)).toBe(1);
    expect(tradeHeatmapIntensity(1, 2)).toBe(0.5);
    expect(tradeHeatmapCellBackground(0, 2)).toContain("244");
    expect(formatTradeHeatmapCaption(response)).toContain("אינסטלציה");
  });
});
