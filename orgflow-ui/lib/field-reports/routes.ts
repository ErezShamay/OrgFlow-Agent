import {
  CAPACITOR_STATIC_EXPORT_PLACEHOLDER_ID,
} from "@/lib/capacitor/build-mode";
import { isCapacitorNativePlatform } from "@/lib/capacitor/platform";

const REPORT_ID_QUERY_KEY = "report";

/** נתיב לעורך דוח - ב-APK (static export) רק `/_/index.html` קיים; UUID ב-query. */
export function fieldReportDetailPath(reportId: string): string {
  if (!reportId) {
    return "/field-reports";
  }

  if (isCapacitorNativePlatform()) {
    const query = new URLSearchParams({
      [REPORT_ID_QUERY_KEY]: reportId,
    });
    return `/field-reports/${CAPACITOR_STATIC_EXPORT_PLACEHOLDER_ID}/?${query.toString()}`;
  }

  return `/field-reports/${reportId}`;
}

export function resolveFieldReportRouteId(
  paramId: string,
  searchParams: Pick<URLSearchParams, "get"> | null | undefined
): string {
  if (paramId === CAPACITOR_STATIC_EXPORT_PLACEHOLDER_ID) {
    return searchParams?.get(REPORT_ID_QUERY_KEY)?.trim() || "";
  }

  return paramId;
}
