import type {
  QualityTradeHeatmapCell,
  QualityTradeHeatmapResponse,
} from "@/lib/quality-issues/types";

export type TradeHeatmapSeverityKey =
  | "open_critical"
  | "open_high"
  | "open_medium"
  | "open_low";

export const TRADE_HEATMAP_SEVERITY_COLUMNS: {
  key: TradeHeatmapSeverityKey;
  label: string;
}[] = [
  { key: "open_critical", label: "קריטי" },
  { key: "open_high", label: "גבוה" },
  { key: "open_medium", label: "בינוני" },
  { key: "open_low", label: "נמוך" },
];

export function maxTradeHeatmapSeverityCount(
  cells: QualityTradeHeatmapCell[]
): number {
  let max = 0;

  for (const cell of cells) {
    for (const column of TRADE_HEATMAP_SEVERITY_COLUMNS) {
      max = Math.max(max, cell[column.key]);
    }
  }

  return max;
}

export function tradeHeatmapIntensity(
  count: number,
  maxCount: number
): number {
  if (count <= 0 || maxCount <= 0) {
    return 0;
  }

  return Math.min(1, count / maxCount);
}

export function tradeHeatmapCellBackground(
  count: number,
  maxCount: number
): string {
  const intensity = tradeHeatmapIntensity(count, maxCount);
  if (intensity <= 0) {
    return "rgb(244 244 245)";
  }

  const alpha = 0.18 + intensity * 0.72;
  return `rgba(7, 116, 141, ${alpha.toFixed(2)})`;
}

export function formatTradeHeatmapCaption(
  response: QualityTradeHeatmapResponse
): string {
  if (response.total_open === 0) {
    return "אין ליקויים פתוחים לפי מלאכה";
  }

  const topTrade = response.cells[0]?.trade;
  if (!topTrade) {
    return `${response.total_open} ליקויים פתוחים לפי מלאכה`;
  }

  return `${response.total_open} ליקויים פתוחים - הכי לחוץ: ${topTrade}`;
}
