"use client";

import { useCallback } from "react";

import LoadingState from "@/components/ui/LoadingState";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { getPortfolioTradeHeatmap } from "@/lib/quality-issues/api";
import { hasQCPermission } from "@/lib/quality-issues/permissions";
import {
  formatTradeHeatmapCaption,
  maxTradeHeatmapSeverityCount,
  TRADE_HEATMAP_SEVERITY_COLUMNS,
  tradeHeatmapCellBackground,
} from "@/lib/quality-issues/trade-heatmap";

export default function PortfolioTradeHeatmapPanel() {
  const effectiveRole = useEffectiveRole();
  const canReadPortfolio = hasQCPermission(
    effectiveRole,
    "quality_portfolio:read"
  );

  const loadHeatmap = useCallback(async () => {
    return getPortfolioTradeHeatmap();
  }, []);

  const { data: heatmap, loading, error } = useOrgQuery(
    "portfolio/quality-trade-heatmap",
    loadHeatmap,
    {
      enabled: canReadPortfolio,
      showErrorToast: false,
    }
  );

  if (!canReadPortfolio) {
    return null;
  }

  if (loading && !heatmap) {
    return (
      <section className="mb-10">
        <LoadingState message="טוען מפת חום לפי מלאכה..." />
      </section>
    );
  }

  if (error && !heatmap) {
    return (
      <section className="of-card of-card-p8 mb-10 text-sm text-red-600 dark:text-red-400">
        {error.message}
      </section>
    );
  }

  if (!heatmap) {
    return null;
  }

  const maxSeverityCount = maxTradeHeatmapSeverityCount(heatmap.cells);

  return (
    <section className="mb-10 space-y-4">
      <div className="space-y-1">
        <p className="text-zinc-500">אנליטיקה</p>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          מפת חום לפי מלאכה
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {formatTradeHeatmapCaption(heatmap)}
        </p>
      </div>

      {heatmap.cells.length === 0 ? (
        <div className="of-card of-card-p8 text-sm text-zinc-600 dark:text-zinc-400">
          אין ליקויים פתוחים לפי מלאכה כרגע.
        </div>
      ) : (
        <div className="of-card of-card-p0 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200 text-start dark:border-zinc-800">
                <th className="px-4 py-3 font-semibold text-zinc-700 dark:text-zinc-300">
                  מלאכה
                </th>
                {TRADE_HEATMAP_SEVERITY_COLUMNS.map((column) => (
                  <th
                    key={column.key}
                    className="px-4 py-3 text-center font-semibold text-zinc-700 dark:text-zinc-300"
                  >
                    {column.label}
                  </th>
                ))}
                <th className="px-4 py-3 text-center font-semibold text-zinc-700 dark:text-zinc-300">
                  סה״כ
                </th>
              </tr>
            </thead>
            <tbody>
              {heatmap.cells.map((cell) => (
                <tr
                  key={cell.trade}
                  className="border-b border-zinc-100 last:border-0 dark:border-zinc-800/80"
                >
                  <td className="px-4 py-3 font-medium text-zinc-900 dark:text-zinc-100">
                    {cell.trade}
                  </td>
                  {TRADE_HEATMAP_SEVERITY_COLUMNS.map((column) => {
                    const count = cell[column.key];
                    return (
                      <td key={column.key} className="px-4 py-3 text-center">
                        <span
                          className="inline-flex min-w-10 justify-center rounded-lg px-2 py-1 font-semibold text-zinc-900 dark:text-zinc-100"
                          style={{
                            backgroundColor: tradeHeatmapCellBackground(
                              count,
                              maxSeverityCount
                            ),
                          }}
                        >
                          {count}
                        </span>
                      </td>
                    );
                  })}
                  <td className="px-4 py-3 text-center font-bold text-zinc-900 dark:text-zinc-100">
                    {cell.open_total}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
