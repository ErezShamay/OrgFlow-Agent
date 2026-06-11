"use client";

import Link from "next/link";
import { useCallback } from "react";

import LoadingState from "@/components/ui/LoadingState";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { getPortfolioQualitySummary } from "@/lib/quality-issues/api";
import {
  formatAverageOpenDays,
  formatProjectQcRankCaption,
  projectQcPressureLevel,
  rankProjectsByQcPressure,
} from "@/lib/quality-issues/portfolio-summary";
import { hasQCPermission } from "@/lib/quality-issues/permissions";
import type { QualityPortfolioProjectSummary } from "@/lib/quality-issues/types";

export default function PortfolioProjectRanking() {
  const effectiveRole = useEffectiveRole();
  const canReadPortfolio = hasQCPermission(
    effectiveRole,
    "quality_portfolio:read"
  );

  const loadSummary = useCallback(async () => {
    return getPortfolioQualitySummary();
  }, []);

  const { data: summary, loading, error } = useOrgQuery(
    "portfolio/quality-summary/ranking",
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
        <LoadingState message="טוען דירוג פרויקטים..." />
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

  const rankedProjects = rankProjectsByQcPressure(summary.projects);
  const rankCaption = formatProjectQcRankCaption(summary.projects);

  return (
    <section className="mb-10 space-y-6">
      <div className="space-y-1">
        <p className="text-zinc-500">דירוג QC</p>
        <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
          דירוג פרויקטים
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {rankCaption}
        </p>
        <p className="text-xs text-zinc-500">
          ממוין לפי ליקויים קריטיים פתוחים, ואז סה״כ ליקויים פתוחים
        </p>
      </div>

      {rankedProjects.length > 0 ? (
        <div className="grid gap-4">
          {rankedProjects.map((project, index) => (
            <PortfolioProjectRankCard
              key={project.project_id}
              rank={index + 1}
              project={project}
            />
          ))}
        </div>
      ) : (
        <div className="of-card of-card-p8 text-sm text-zinc-600 dark:text-zinc-400">
          אין פרויקטים בתיק
        </div>
      )}
    </section>
  );
}

function PortfolioProjectRankCard({
  rank,
  project,
}: {
  rank: number;
  project: QualityPortfolioProjectSummary;
}) {
  const pressure = projectQcPressureLevel(project);
  const pressureClass =
    pressure === "critical"
      ? "border-red-200 dark:border-red-900"
      : pressure === "open"
        ? "border-amber-200 dark:border-amber-900"
        : "border-zinc-200 dark:border-zinc-800";

  return (
    <div className={`of-card of-card-p6 ${pressureClass}`}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div
            className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-lg font-black ${
              pressure === "critical"
                ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
                : pressure === "open"
                  ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                  : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
            }`}
          >
            {rank}
          </div>

          <div className="space-y-2">
            <h3 className="text-xl font-bold">
              <Link
                href={`/projects/${encodeURIComponent(project.project_id)}/issues`}
                className="text-brand hover:underline dark:text-brand-light"
              >
                {project.project_name?.trim() || "פרויקט"}
              </Link>
            </h3>

            <div className="flex flex-wrap gap-2 text-xs">
              <RankBadge
                label={`פתוחים: ${project.open_total}`}
                tone={project.open_total > 0 ? "neutral" : "muted"}
              />
              <RankBadge
                label={`קריטיים: ${project.open_critical}`}
                tone={project.open_critical > 0 ? "danger" : "muted"}
              />
              {project.critical_open_over_14_days > 0 ? (
                <RankBadge
                  label={`קריטיים > 14 יום: ${project.critical_open_over_14_days}`}
                  tone="danger"
                />
              ) : null}
              {project.average_open_days != null ? (
                <RankBadge
                  label={`ממוצע: ${formatAverageOpenDays(project.average_open_days)}`}
                  tone={
                    project.average_open_days > 14 ? "warn" : "neutral"
                  }
                />
              ) : null}
            </div>
          </div>
        </div>

        <Link
          href={`/projects/${encodeURIComponent(project.project_id)}/issues`}
          className="text-sm font-medium text-brand hover:underline dark:text-brand-light"
        >
          צפה בליקויים
        </Link>
      </div>
    </div>
  );
}

function RankBadge({
  label,
  tone,
}: {
  label: string;
  tone: "danger" | "warn" | "neutral" | "muted";
}) {
  const className =
    tone === "danger"
      ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
      : tone === "warn"
        ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
        : tone === "muted"
          ? "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
          : "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";

  return (
    <span className={`rounded-full px-3 py-1 ${className}`}>
      {label}
    </span>
  );
}
