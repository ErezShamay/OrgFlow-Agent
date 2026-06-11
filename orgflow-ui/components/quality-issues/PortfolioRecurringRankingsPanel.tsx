"use client";

import Link from "next/link";
import { useCallback } from "react";

import LoadingState from "@/components/ui/LoadingState";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { getPortfolioRecurringRankings } from "@/lib/quality-issues/api";
import { hasQCPermission } from "@/lib/quality-issues/permissions";
import {
  buildProjectIssueHref,
  formatContractorRecurringSubtitle,
  formatRecurringIssueSubtitle,
  formatRecurringRankingsCaption,
} from "@/lib/quality-issues/recurring-rankings";

export default function PortfolioRecurringRankingsPanel() {
  const effectiveRole = useEffectiveRole();
  const canReadPortfolio = hasQCPermission(
    effectiveRole,
    "quality_portfolio:read"
  );

  const loadRankings = useCallback(async () => {
    return getPortfolioRecurringRankings();
  }, []);

  const { data: rankings, loading, error } = useOrgQuery(
    "portfolio/quality-recurring-rankings",
    loadRankings,
    {
      enabled: canReadPortfolio,
      showErrorToast: false,
    }
  );

  if (!canReadPortfolio) {
    return null;
  }

  if (loading && !rankings) {
    return (
      <section className="mb-10">
        <LoadingState message="טוען דירוג ליקויים חוזרים..." />
      </section>
    );
  }

  if (error && !rankings) {
    return (
      <section className="of-card of-card-p8 mb-10 text-sm text-red-600 dark:text-red-400">
        {error.message}
      </section>
    );
  }

  if (!rankings) {
    return null;
  }

  const caption = formatRecurringRankingsCaption(rankings);

  return (
    <section className="mb-10 space-y-6">
      <div className="space-y-1">
        <p className="text-zinc-500">אנליטיקה</p>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          ליקויים חוזרים וקבלני משנה
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">{caption}</p>
      </div>

      {rankings.total_recurring === 0 ? (
        <div className="of-card of-card-p8 text-sm text-zinc-600 dark:text-zinc-400">
          אין ליקויים חוזרים כרגע - ליקוי שחוזר אחרי סגירה יופיע כאן.
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="of-card of-card-p0 overflow-hidden">
            <div className="border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
              <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                ליקויים חוזרים
              </h3>
              <p className="text-xs text-zinc-500">
                ממוין לפי מספר חזרות, חומרה וכותרת
              </p>
            </div>
            <ol className="divide-y divide-zinc-100 dark:divide-zinc-800/80">
              {rankings.issues.map((entry, index) => (
                <li key={entry.issue_id} className="px-4 py-3">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-xs font-bold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200">
                      {index + 1}
                    </span>
                    <div className="min-w-0 flex-1 space-y-1">
                      <Link
                        href={buildProjectIssueHref(
                          entry.project_id,
                          entry.issue_id
                        )}
                        className="font-medium text-zinc-900 hover:text-[var(--of-teal)] dark:text-zinc-100"
                      >
                        {entry.title}
                      </Link>
                      <p className="text-xs text-zinc-500">
                        {formatRecurringIssueSubtitle(entry)}
                      </p>
                    </div>
                    <div className="shrink-0 text-end">
                      <p className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                        {entry.recurrence_count}
                      </p>
                      <p className="text-xs text-zinc-500">חזרות</p>
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="of-card of-card-p0 overflow-hidden">
            <div className="border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
              <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                קבלני משנה
              </h3>
              <p className="text-xs text-zinc-500">
                לפי מספר ליקויים חוזרים בפרויקטים
              </p>
            </div>
            <ol className="divide-y divide-zinc-100 dark:divide-zinc-800/80">
              {rankings.contractors.map((entry, index) => (
                <li key={entry.contractor_name} className="px-4 py-3">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-xs font-bold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200">
                      {index + 1}
                    </span>
                    <div className="min-w-0 flex-1 space-y-1">
                      <p className="font-medium text-zinc-900 dark:text-zinc-100">
                        {entry.contractor_name}
                      </p>
                      <p className="text-xs text-zinc-500">
                        {formatContractorRecurringSubtitle(entry)}
                      </p>
                    </div>
                    <div className="shrink-0 text-end">
                      <p className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                        {entry.recurring_issue_count}
                      </p>
                      <p className="text-xs text-zinc-500">ליקויים</p>
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </section>
  );
}
