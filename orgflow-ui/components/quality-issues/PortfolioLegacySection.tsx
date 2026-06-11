"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import LoadingState from "@/components/ui/LoadingState";
import PageLoadingOverlay from "@/components/ui/PageLoadingOverlay";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { apiFetch } from "@/lib/api/client";
import {
  PORTFOLIO_LEGACY_DEFAULT_EXPANDED,
  PORTFOLIO_LEGACY_RANKING_TITLE,
  PORTFOLIO_LEGACY_SECTION_HINT,
  PORTFOLIO_LEGACY_SECTION_SUMMARY,
  PORTFOLIO_LEGACY_SECTION_TITLE,
  portfolioLegacySectionId,
} from "@/lib/quality-issues/portfolio-page";
import { DEFAULT_QUERY_TTL_MS } from "@/lib/ui/query-cache";

type Prediction = {
  prediction: string;
  risk_score: number;
  message: string;
};

type PortfolioProject = {
  project_id: string;
  project_name: string;
  health: {
    score: number;
    status: string;
  };
  summary: {
    actions_count: number;
    escalations_count: number;
    reviews_count: number;
  };
  prediction: Prediction;
};

type PortfolioResponse = {
  projects: PortfolioProject[];
  critical_projects: number;
  total_projects: number;
  total_actions: number;
  total_escalations: number;
  average_health_score: number;
};

export default function PortfolioLegacySection() {
  const [expanded, setExpanded] = useState(PORTFOLIO_LEGACY_DEFAULT_EXPANDED);

  const loadPortfolio = useCallback(async () => {
    const response = await apiFetch("/portfolio/summary");

    if (!response.ok) {
      throw new Error("Failed loading legacy portfolio");
    }

    return (await response.json()) as PortfolioResponse;
  }, []);

  const {
    data: portfolio,
    loading,
    isValidating,
    error,
  } = useOrgQuery("portfolio/summary", loadPortfolio, {
    enabled: expanded,
    ttlMs: DEFAULT_QUERY_TTL_MS,
    showErrorToast: false,
  });

  return (
    <section
      id={portfolioLegacySectionId()}
      className="mt-12 border-t border-zinc-200 pt-10 dark:border-zinc-800"
      aria-label={PORTFOLIO_LEGACY_SECTION_TITLE}
    >
      <button
        type="button"
        className="flex w-full items-start justify-between gap-4 text-start"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
      >
        <div className="space-y-1">
          <p className="text-zinc-500">{PORTFOLIO_LEGACY_SECTION_TITLE}</p>
          <h2 className="text-xl font-semibold text-zinc-800 dark:text-zinc-200">
            {PORTFOLIO_LEGACY_SECTION_SUMMARY}
          </h2>
          <p className="text-sm text-zinc-500">{PORTFOLIO_LEGACY_SECTION_HINT}</p>
        </div>
        <span className="shrink-0 text-sm text-zinc-500">
          {expanded ? "הסתר" : "הצג"}
        </span>
      </button>

      {expanded ? (
        <div className="mt-8 space-y-10">
          {loading && !portfolio ? (
            <LoadingState message="טוען סקירה תפעולית..." />
          ) : null}

          {error && !portfolio ? (
            <div className="of-card of-card-p8 text-sm text-red-600 dark:text-red-400">
              {error.message}
            </div>
          ) : null}

          {portfolio ? (
            <>
              {isValidating ? <PageLoadingOverlay /> : null}

              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-5">
                <LegacyKpiCard title="סה״כ פרויקטים" value={portfolio.total_projects} />
                <LegacyKpiCard
                  title="פרויקטים קריטיים"
                  value={portfolio.critical_projects}
                  danger
                />
                <LegacyKpiCard title="סה״כ פעולות" value={portfolio.total_actions} />
                <LegacyKpiCard
                  title="סה״כ הסלמות"
                  value={portfolio.total_escalations}
                  danger
                />
                <LegacyKpiCard
                  title="Health ממוצע"
                  value={portfolio.average_health_score}
                />
              </div>

              <div>
                <h3 className="mb-6 text-2xl font-bold">
                  {PORTFOLIO_LEGACY_RANKING_TITLE}
                </h3>

                <div className="grid gap-6">
                  {portfolio.projects.map((project) => (
                    <div key={project.project_id} className="of-card of-card-p8">
                      <div className="flex flex-wrap items-start justify-between gap-6">
                        <div className="flex-1">
                          <h4 className="text-2xl font-bold">
                            <Link
                              href={`/projects/${project.project_id}`}
                              className="hover:underline"
                            >
                              {project.project_name}
                            </Link>
                          </h4>

                          <div className="mt-4 flex flex-wrap gap-3">
                            <LegacyBadge>
                              פעולות: {project.summary.actions_count}
                            </LegacyBadge>
                            <LegacyBadge>
                              הסלמות: {project.summary.escalations_count}
                            </LegacyBadge>
                            <LegacyBadge>
                              ביקורות: {project.summary.reviews_count}
                            </LegacyBadge>
                          </div>

                          <div className="mt-6 rounded-2xl border border-zinc-200 p-5 dark:border-zinc-700">
                            <div className="mb-3 flex flex-wrap items-center gap-3">
                              <PredictionBadge
                                prediction={project.prediction.prediction}
                              />
                              <span className="text-sm text-zinc-500">
                                Risk Score: {project.prediction.risk_score}
                              </span>
                            </div>
                            <p className="leading-7 text-zinc-700 dark:text-zinc-300">
                              {project.prediction.message}
                            </p>
                          </div>
                        </div>

                        <div className="text-center">
                          <HealthScoreCircle score={project.health.score} />
                          <p className="mt-3 text-zinc-500">Health</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function LegacyKpiCard({
  title,
  value,
  danger = false,
}: {
  title: string;
  value: number;
  danger?: boolean;
}) {
  return (
    <div
      className={`of-kpi-card ${danger ? "border-red-200 dark:border-red-900" : ""}`}
    >
      <p className={`mb-3 ${danger ? "text-red-500" : "text-zinc-500"}`}>
        {title}
      </p>
      <p className={`text-5xl font-black ${danger ? "text-red-600" : ""}`}>
        {value}
      </p>
    </div>
  );
}

function LegacyBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs dark:bg-zinc-800">
      {children}
    </span>
  );
}

function HealthScoreCircle({ score }: { score: number }) {
  const toneClass =
    score >= 80
      ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
      : score >= 50
        ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
        : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300";

  return (
    <div
      className={`flex h-24 w-24 items-center justify-center rounded-full text-3xl font-black ${toneClass}`}
    >
      {score}
    </div>
  );
}

function PredictionBadge({ prediction }: { prediction: string }) {
  if (prediction === "HIGH_RISK") {
    return (
      <span className="rounded-full bg-red-600 px-3 py-1 text-xs text-white">
        סיכון גבוה
      </span>
    );
  }

  if (prediction === "MEDIUM_RISK") {
    return (
      <span className="rounded-full bg-yellow-500 px-3 py-1 text-xs text-white">
        סיכון בינוני
      </span>
    );
  }

  return (
    <span className="rounded-full bg-green-600 px-3 py-1 text-xs text-white">
      סיכון נמוך
    </span>
  );
}
