"use client";

import { useCallback, useMemo } from "react";

import LoadingState from "@/components/ui/LoadingState";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { usePortfolioLiveUpdates } from "@/hooks/usePortfolioLiveUpdates";
import { getPortfolioQualitySummary } from "@/lib/quality-issues/api";
import {
  formatLastReportAtCaption,
  formatLastReportAtKpi,
  formatOpenIssuesPerProjectCaption,
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

  const { snapshot: liveSnapshot, isLive } = usePortfolioLiveUpdates(
    canReadPortfolio
  );

  const displayOpenTotal = liveSnapshot?.total_open ?? summary?.total_open ?? 0;
  const displayOpenCritical =
    liveSnapshot?.total_open_critical ?? summary?.total_open_critical ?? 0;

  const liveCaption = useMemo(() => {
    if (!isLive || !liveSnapshot?.updated_at) {
      return null;
    }

    const updatedAt = new Date(liveSnapshot.updated_at);
    if (Number.isNaN(updatedAt.getTime())) {
      return "עדכון חי";
    }

    return `עדכון חי — ${updatedAt.toLocaleTimeString("he-IL", {
      hour: "2-digit",
      minute: "2-digit",
    })}`;
  }, [isLive, liveSnapshot?.updated_at]);

  if (!canReadPortfolio) {
    return null;
  }

  if (loading && !summary) {
    return (
      <section className="mb-10">
        <LoadingState message="טוען סיכום תיק פיקוח..." />
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
  const lastReportCaption = formatLastReportAtCaption(summary.last_report_at);

  return (
    <section className="mb-10 space-y-6">
      <div className="space-y-1">
        <p className="text-zinc-500">תיק פיקוח</p>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          תיק פיקוח הנדסי — ליקויים שפורסמו
        </h2>
        {liveCaption ? (
          <p className="text-sm font-medium text-emerald-700 dark:text-emerald-400">
            {liveCaption}
          </p>
        ) : null}
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {projectCaption}
        </p>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {lastReportCaption}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <SupervisionKpiCard
          title="ליקויים פתוחים"
          value={displayOpenTotal}
          live={isLive}
        />
        <SupervisionKpiCard
          title="קריטיים פתוחים"
          value={displayOpenCritical}
          danger={displayOpenCritical > 0}
          live={isLive}
        />
        <SupervisionKpiCard
          title="דוח אחרון"
          value={formatLastReportAtKpi(summary.last_report_at)}
          text
        />
      </div>
    </section>
  );
}

function SupervisionKpiCard({
  title,
  value,
  danger = false,
  text = false,
  live = false,
}: {
  title: string;
  value: number | string;
  danger?: boolean;
  text?: boolean;
  live?: boolean;
}) {
  const borderClass = danger ? "border-red-200 dark:border-red-900" : "";
  const titleClass = danger ? "text-red-500" : "text-zinc-500";
  const valueClass = danger ? "text-red-600" : "";

  return (
    <div className={`of-kpi-card ${borderClass}`}>
      <p className={`mb-3 ${titleClass}`}>
        {title}
        {live ? (
          <span className="ms-2 inline-block h-2 w-2 rounded-full bg-emerald-500 align-middle" />
        ) : null}
      </p>
      <p
        className={`font-black ${text ? "text-3xl" : "text-5xl"} ${valueClass}`}
      >
        {value}
      </p>
    </div>
  );
}
