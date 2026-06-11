"use client";

import { useCallback } from "react";

import LoadingState from "@/components/ui/LoadingState";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { getPortfolioQualitySummary } from "@/lib/quality-issues/api";
import {
  formatAverageOpenDays,
  formatAverageOpenDaysCaption,
  formatClosedWithin30DaysCaption,
  formatClosedWithin30DaysPercent,
  formatCriticalOpenOver14DaysCaption,
  formatOpenIssuesPerProjectCaption,
  isAverageOpenDaysHealthy,
  isClosedWithin30DaysHealthy,
} from "@/lib/quality-issues/portfolio-summary";
import { hasQCPermission } from "@/lib/quality-issues/permissions";

export default function PortfolioQualitySummaryPanel() {
  const effectiveRole = useEffectiveRole();
  const canReadPortfolio = hasQCPermission(
    effectiveRole,
    "quality_portfolio:read"
  );

  const loadSummary = useCallback(async () => {
    return getPortfolioQualitySummary();
  }, []);

  const { data: summary, loading, error } = useOrgQuery(
    "portfolio/quality-summary",
    loadSummary,
    {
      enabled: canReadPortfolio,
      showErrorToast: false,
    }
  );

  if (!canReadPortfolio) {
    return null;
  }

  if (loading && !summary) {
    return (
      <section className="mb-10">
        <LoadingState message="טוען סיכום בקרת איכות..." />
      </section>
    );
  }

  if (error && !summary) {
    return (
      <section className="of-card of-card-p8 mb-10 text-sm text-red-600 dark:text-red-400">
        {error.message}
      </section>
    );
  }

  if (!summary) {
    return null;
  }

  const projectCaption = formatOpenIssuesPerProjectCaption(summary.projects);
  const staleCriticalCaption = formatCriticalOpenOver14DaysCaption(summary);
  const closedWithin30Caption = formatClosedWithin30DaysCaption(summary);
  const closedWithin30Healthy = isClosedWithin30DaysHealthy(
    summary.closed_within_30_days_percent
  );
  const averageOpenDaysCaption = formatAverageOpenDaysCaption(summary);
  const averageOpenDaysHealthy = isAverageOpenDaysHealthy(
    summary.average_open_days
  );

  return (
    <section className="mb-10 space-y-6">
      <div className="space-y-1">
        <p className="text-zinc-500">בקרת איכות</p>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          תיק QC - ליקויים פתוחים
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {projectCaption}
        </p>
        <p
          className={`text-sm ${
            summary.critical_open_over_14_days > 0
              ? "text-red-600 dark:text-red-400"
              : "text-zinc-600 dark:text-zinc-400"
          }`}
        >
          {staleCriticalCaption}
        </p>
        <p
          className={`text-sm ${
            summary.closed_within_30_days_percent == null
              ? "text-zinc-600 dark:text-zinc-400"
              : closedWithin30Healthy
                ? "text-green-700 dark:text-green-400"
                : "text-amber-700 dark:text-amber-400"
          }`}
        >
          {closedWithin30Caption}
        </p>
        <p
          className={`text-sm ${
            summary.average_open_days == null
              ? "text-zinc-600 dark:text-zinc-400"
              : averageOpenDaysHealthy
                ? "text-green-700 dark:text-green-400"
                : "text-amber-700 dark:text-amber-400"
          }`}
        >
          {averageOpenDaysCaption}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-5">
        <QcKpiCard
          title="ליקויים פתוחים"
          value={summary.total_open}
        />
        <QcKpiCard
          title="קריטיים פתוחים"
          value={summary.total_open_critical}
          danger={summary.total_open_critical > 0}
        />
        <QcKpiCard
          title="קריטיים > 14 יום"
          value={summary.critical_open_over_14_days}
          danger={summary.critical_open_over_14_days > 0}
        />
        <QcKpiCard
          title="סגירה תוך 30 יום"
          value={formatClosedWithin30DaysPercent(
            summary.closed_within_30_days_percent
          )}
          text
          success={
            summary.closed_within_30_days_percent != null
            && closedWithin30Healthy
          }
          warn={
            summary.closed_within_30_days_percent != null
            && !closedWithin30Healthy
          }
        />
        <QcKpiCard
          title="ממוצע ימים פתוח"
          value={formatAverageOpenDays(summary.average_open_days)}
          text
          success={
            summary.average_open_days != null && averageOpenDaysHealthy
          }
          warn={
            summary.average_open_days != null && !averageOpenDaysHealthy
          }
        />
      </div>
    </section>
  );
}

function QcKpiCard({
  title,
  value,
  danger = false,
  success = false,
  warn = false,
  text = false,
}: {
  title: string;
  value: number | string;
  danger?: boolean;
  success?: boolean;
  warn?: boolean;
  text?: boolean;
}) {
  const borderClass = danger
    ? "border-red-200 dark:border-red-900"
    : success
      ? "border-green-200 dark:border-green-900"
      : warn
        ? "border-amber-200 dark:border-amber-900"
        : "";
  const titleClass = danger
    ? "text-red-500"
    : success
      ? "text-green-600 dark:text-green-400"
      : warn
        ? "text-amber-600 dark:text-amber-400"
        : "text-zinc-500";
  const valueClass = danger
    ? "text-red-600"
    : success
      ? "text-green-700 dark:text-green-300"
      : warn
        ? "text-amber-700 dark:text-amber-300"
        : "";

  return (
    <div className={`of-kpi-card ${borderClass}`}>
      <p className={`mb-3 ${titleClass}`}>
        {title}
      </p>
      <p
        className={`font-black ${text ? "text-3xl" : "text-5xl"} ${valueClass}`}
      >
        {value}
      </p>
    </div>
  );
}
