"use client";

import { useMemo } from "react";

import {
  resolveFieldReportDataSource,
  type FieldReportDataSource,
  type FieldReportDataSourceContext,
} from "@/lib/field-reports/data-source";
import { useFieldReportNetworkStatus } from "@/hooks/useFieldReportNetworkStatus";

export type UseFieldReportDataSourceResult = FieldReportDataSource & {
  /** בודק מחדש נגישות API (למשל אחרי חזרת רשת). */
  refreshNetwork: () => Promise<void>;
  /** האם ריצת ping פעילה. */
  pinging: boolean;
};

/**
 * מצב מקור נתונים לדוחות - `navigator.onLine` + ping ל-module-status.
 * העבר `hasLocalReport` / `serverReportId` כשטוענים דוח (FR-012+).
 */
export function useFieldReportDataSource(
  context: FieldReportDataSourceContext = {}
): UseFieldReportDataSourceResult {
  const { snapshot, checking, refresh } = useFieldReportNetworkStatus();

  const dataSource = useMemo(
    () => resolveFieldReportDataSource(snapshot, context),
    [
      snapshot.navigatorOnline,
      snapshot.apiReachable,
      context.hasLocalReport,
      context.serverReportId,
    ]
  );

  return {
    ...dataSource,
    refreshNetwork: refresh,
    pinging: checking,
  };
}
