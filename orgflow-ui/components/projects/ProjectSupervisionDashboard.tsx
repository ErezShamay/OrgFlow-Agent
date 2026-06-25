"use client";

import Link from "next/link";
import { useCallback } from "react";

import ProjectApartmentProgressGrid from "@/components/projects/ProjectApartmentProgressGrid";
import ProjectFieldReportLink from "@/components/field-reports/ProjectFieldReportLink";
import ProjectSupervisionKpiRow from "@/components/projects/ProjectSupervisionKpiRow";
import ProjectTradeProgressPanel from "@/components/projects/ProjectTradeProgressPanel";
import Badge from "@/components/ui/Badge";
import LoadingState from "@/components/ui/LoadingState";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import {
  fetchProjectSupervisionDashboard,
  SUPERVISION_OVERALL_STATUS_BADGE,
  SUPERVISION_OVERALL_STATUS_LABELS,
} from "@/lib/projects/supervision-dashboard";
import { projectFieldReportsListPath } from "@/lib/field-reports/routes";

type ProjectSupervisionDashboardProps = {
  projectId: string;
};

export default function ProjectSupervisionDashboard({
  projectId,
}: ProjectSupervisionDashboardProps) {
  const loadDashboard = useCallback(async () => {
    return fetchProjectSupervisionDashboard(projectId);
  }, [projectId]);

  const { data, loading, error } = useOrgQuery(
    `projects/${projectId}/supervision-dashboard`,
    loadDashboard,
    {
      showErrorToast: false,
    }
  );

  if (loading && !data) {
    return <LoadingState message="טוען דשבורד פרויקט..." />;
  }

  if (error && !data) {
    return (
      <section className="of-card of-card-p8 text-sm text-red-600 dark:text-red-400">
        {error.message}
      </section>
    );
  }

  if (!data) {
    return (
      <section className="of-card of-card-p8 text-sm text-zinc-500">
        אין נתוני דשבורד זמינים לפרויקט זה.
      </section>
    );
  }

  const statusBadge = SUPERVISION_OVERALL_STATUS_BADGE[data.overall_status];
  const statusLabel = SUPERVISION_OVERALL_STATUS_LABELS[data.overall_status];
  const isEmpty =
    data.kpis.total_items === 0
    && data.trades.length === 0
    && data.apartments.length === 0
    && data.public_areas.length === 0;

  return (
    <div className="space-y-8" dir="rtl">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="of-page-title">{data.project_name}</h1>
            <Badge variant={statusBadge}>{statusLabel}</Badge>
          </div>
          <p className="of-page-desc">דשבורד פיקוח הנדסי</p>
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <Link
              href={`/projects/${encodeURIComponent(projectId)}/settings`}
              className="font-medium text-brand hover:underline dark:text-brand-light"
            >
              הגדרות פרויקט
            </Link>
            <Link
              href={`/projects/${encodeURIComponent(projectId)}/issues`}
              className="font-medium text-brand hover:underline dark:text-brand-light"
            >
              כל הליקויים
            </Link>
            <Link
              href={projectFieldReportsListPath(projectId)}
              className="font-medium text-brand hover:underline dark:text-brand-light"
            >
              דוחות שטח
            </Link>
            <ProjectFieldReportLink projectId={projectId} />
          </div>
        </div>
      </header>

      {isEmpty ? (
        <section className="of-card of-card-p8 text-sm text-zinc-600 dark:text-zinc-400">
          אין עדיין דוחות שטח סגורים או ליקויים מפורסמים לפרויקט זה. התחילו
          ב«תיעוד ביקור» או ביצירת דוח שטח חדש.
        </section>
      ) : null}

      <ProjectSupervisionKpiRow kpis={data.kpis} />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <ProjectTradeProgressPanel projectId={projectId} trades={data.trades} />
        <ProjectApartmentProgressGrid
          projectId={projectId}
          apartments={data.apartments}
          publicAreas={data.public_areas}
        />
      </div>
    </div>
  );
}
