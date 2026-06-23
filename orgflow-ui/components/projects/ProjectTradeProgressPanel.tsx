"use client";

import Link from "next/link";

import {
  projectSupervisionTradePagePath,
  supervisionTradeBarColor,
  type SupervisionTradeProgress,
} from "@/lib/projects/supervision-dashboard-types";

type ProjectTradeProgressPanelProps = {
  projectId: string;
  trades: SupervisionTradeProgress[];
};

export default function ProjectTradeProgressPanel({
  projectId,
  trades,
}: ProjectTradeProgressPanelProps) {
  return (
    <section className="of-card of-card-p6 shadow-sm" dir="rtl">
      <h2 className="mb-6 text-xl font-bold text-zinc-900 dark:text-zinc-100">
        התקדמות לפי קטגוריה
      </h2>

      {trades.length === 0 ? (
        <p className="text-sm text-zinc-500">
          אין עדיין נתוני מלאכות מדוחות שטח סגורים.
        </p>
      ) : (
        <ul className="space-y-5">
          {trades.map((trade, index) => (
            <li key={trade.trade_key}>
              <Link
                href={projectSupervisionTradePagePath(projectId, trade.trade_key)}
                className="block rounded-xl p-2 transition hover:bg-zinc-50 dark:hover:bg-zinc-800/60"
              >
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="font-medium text-zinc-900 dark:text-zinc-100">
                    {trade.label_he} ({trade.total_items})
                  </span>
                  <span
                    className="text-sm font-semibold text-zinc-600 dark:text-zinc-300"
                    dir="ltr"
                  >
                    {trade.progress_percent}%
                  </span>
                </div>
                <div
                  className="h-2.5 overflow-hidden rounded-full bg-zinc-200/80 dark:bg-zinc-700"
                  role="progressbar"
                  aria-valuenow={trade.progress_percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${trade.label_he} — ${trade.progress_percent}%`}
                >
                  <div
                    className={`h-full rounded-full transition-all ${supervisionTradeBarColor(index)}`}
                    style={{
                      width: `${Math.min(100, Math.max(0, trade.progress_percent))}%`,
                    }}
                  />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
