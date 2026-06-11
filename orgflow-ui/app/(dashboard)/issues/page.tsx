"use client";

import { useCallback, useMemo, useState } from "react";

import ContractorIssuesBanner from "@/components/quality-issues/ContractorIssuesBanner";
import IssuesFilters from "@/components/quality-issues/IssuesFilters";
import IssuesTable from "@/components/quality-issues/IssuesTable";
import LoadingState from "@/components/ui/LoadingState";
import PageHeader from "@/components/ui/PageHeader";
import PageLoadingOverlay from "@/components/ui/PageLoadingOverlay";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { apiFetch } from "@/lib/api/client";
import { listOrganizationQualityIssues } from "@/lib/quality-issues/api";
import {
  contractorIssuesEmptyMessage,
  contractorIssuesPageDescription,
  contractorIssuesPageTitle,
  isContractorIssuesView,
} from "@/lib/quality-issues/contractor-issues-view";
import {
  createEmptyIssuesFilterState,
  hasActiveIssuesFilters,
  issuesFilterStateToListQuery,
  serializeIssuesFilterKey,
  type IssuesFilterState,
} from "@/lib/quality-issues/filters";
import { hasQCPermission } from "@/lib/quality-issues/permissions";

type ProjectSummary = {
  id: string;
  project_name: string;
};

export default function OrganizationIssuesPage() {
  const effectiveRole = useEffectiveRole();
  const canReadIssues = hasQCPermission(
    effectiveRole,
    "quality_issues:read"
  );
  const contractorView = isContractorIssuesView(effectiveRole);
  const [filters, setFilters] = useState<IssuesFilterState>(
    createEmptyIssuesFilterState
  );

  const loadProjects = useCallback(async () => {
    const response = await apiFetch("/projects");
    if (!response.ok) {
      throw new Error("שגיאה בטעינת פרויקטים");
    }

    return (await response.json()) as ProjectSummary[];
  }, []);

  const {
    data: projects,
    loading: loadingProjects,
  } = useOrgQuery("projects/summary-for-issues", loadProjects, {
    enabled: canReadIssues,
  });

  const projectNames = useMemo(() => {
    const map: Record<string, string> = {};
    for (const project of projects ?? []) {
      map[project.id] = project.project_name;
    }
    return map;
  }, [projects]);

  const loadIssues = useCallback(async () => {
    return listOrganizationQualityIssues(
      issuesFilterStateToListQuery(filters, effectiveRole)
    );
  }, [filters, effectiveRole]);

  const filterKey = serializeIssuesFilterKey(filters, effectiveRole);

  const {
    data: issuesResponse,
    loading,
    isValidating,
    error,
    reload,
  } = useOrgQuery(`issues?${filterKey}`, loadIssues, {
    enabled: canReadIssues,
    showErrorToast: true,
    errorMessage: "שגיאה בטעינת ליקויים",
  });

  if (!canReadIssues) {
    return (
      <main className="of-dashboard-page">
        <div className="mx-auto max-w-6xl">
          <PageHeader
            title="ליקויים"
            description="אין הרשאה לצפייה ברשימת הליקויים"
          />
        </div>
      </main>
    );
  }

  if ((loading || loadingProjects) && !issuesResponse) {
    return (
      <main className="of-dashboard-page">
        <LoadingState message="טוען ליקויים..." />
      </main>
    );
  }

  const issues = issuesResponse?.items ?? [];
  const total = issuesResponse?.total ?? 0;
  const filtersActive = hasActiveIssuesFilters(filters);

  return (
    <main className="of-dashboard-page">
      {isValidating ? <PageLoadingOverlay /> : null}

      <div className="mx-auto max-w-6xl space-y-6">
        <PageHeader
          eyebrow="בקרת איכות"
          title={contractorView ? contractorIssuesPageTitle() : "ליקויים"}
          description={
            contractorView
              ? contractorIssuesPageDescription()
              : "מעקב ליקויים חיים בכל הפרויקטים - ממצאים מדוחות שטח שנסגרו"
          }
          actions={
            <button
              type="button"
              onClick={() => void reload()}
              className="
                rounded-2xl
                border
                border-zinc-300
                px-4
                py-2
                text-sm
                font-semibold
                transition
                hover:bg-zinc-100
                dark:border-zinc-700
                dark:hover:bg-zinc-800
              "
            >
              רענון
            </button>
          }
        />

        {contractorView ? <ContractorIssuesBanner /> : null}

        <IssuesFilters
          value={filters}
          onChange={setFilters}
          role={effectiveRole}
        />

        {error && !issuesResponse ? (
          <div className="of-card of-card-p8 text-sm text-red-600 dark:text-red-400">
            {error.message}
          </div>
        ) : null}

        {!loading && issues.length === 0 ? (
          <div className="of-card of-card-p8">
            <p className="font-medium">
              {contractorView
                ? contractorIssuesEmptyMessage(filtersActive)
                : filtersActive
                  ? "אין ליקויים התואמים את הסינון"
                  : "אין ליקויים רשומים בארגון"}
            </p>
            <p className="mt-2 text-sm text-zinc-500">
              {contractorView
                ? "כשמפקח יפתח ליקוי חדש או יסמן ליקוי בטיפול - הוא יופיע כאן."
                : filtersActive
                  ? "נסה לשנות את הסטטוס, החומרה או המלאכה - או נקה את הסינון."
                  : "ליקויים נוצרים אוטומטית כשמפקח סוגר דוח ביקור עם ממצאים."}
            </p>
          </div>
        ) : null}

        <IssuesTable
          issues={issues}
          projectNames={projectNames}
          showProjectColumn
          total={total}
        />
      </div>
    </main>
  );
}
