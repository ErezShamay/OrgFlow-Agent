import type { QualityIssueVisitDiffResponse } from "@/lib/quality-issues/types";
import { VISIT_ISSUE_DIFF_BUCKET_ORDER } from "@/lib/quality-issues/visit-issue-diff";

export const PDF_ISSUE_MARKER_COLUMN_HEADER_HE = "סטטוס ליקוי";

/** תוויות PDF - «עדיין פתוח» ב-UI מוצג כ«פתוח מביקור קודם» בדוח. */
export const PDF_ISSUE_MARKER_LABELS_HE = {
  new: "חדש",
  still_open: "פתוח מביקור קודם",
  closed: "נסגר",
  recurring: "חוזר",
} as const;

export type PdfLineIssueMarkerMap = ReadonlyMap<string, string>;

export function hasPdfIssueMarkers(
  markers: PdfLineIssueMarkerMap | undefined
): markers is PdfLineIssueMarkerMap {
  return Boolean(markers && markers.size > 0);
}

export function buildLineIssueMarkerMapFromVisitDiff(
  diff: QualityIssueVisitDiffResponse
): Map<string, string> {
  const map = new Map<string, string>();

  for (const category of VISIT_ISSUE_DIFF_BUCKET_ORDER) {
    const label = PDF_ISSUE_MARKER_LABELS_HE[category];

    for (const entry of diff[category]) {
      const lineId = entry.line_id?.trim();
      if (!lineId || map.has(lineId)) {
        continue;
      }

      map.set(lineId, label);
    }
  }

  return map;
}

export function resolvePdfIssueMarkerForLine(
  lineId: string,
  markers: PdfLineIssueMarkerMap | undefined
): string {
  if (!markers) {
    return "";
  }

  return markers.get(lineId) ?? "";
}
