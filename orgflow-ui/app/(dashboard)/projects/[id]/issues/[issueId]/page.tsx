"use client";

import Link from "next/link";
import { use, useCallback } from "react";

import IssueDetailPanel from "@/components/quality-issues/IssueDetailPanel";
import LoadingState from "@/components/ui/LoadingState";
import PageHeader from "@/components/ui/PageHeader";
import PageLoadingOverlay from "@/components/ui/PageLoadingOverlay";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { getQualityIssueDetail } from "@/lib/quality-issues/api";
import { issueBelongsToProject } from "@/lib/quality-issues/issue-detail";
import { hasQCPermission } from "@/lib/quality-issues/permissions";

type Props = {
  params: Promise<{
    id: string;
    issueId: string;
  }>;
};

export default function ProjectIssueDetailPage({ params }: Props) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;
  const issueId = resolvedParams.issueId;
  const effectiveRole = useEffectiveRole();
  const canReadIssues = hasQCPermission(
    effectiveRole,
    "quality_issues:read"
  );

  const loadIssueDetail = useCallback(async () => {
    return getQualityIssueDetail(issueId);
  }, [issueId]);

  const {
    data: detail,
    loading,
    isValidating,
    error,
    reload,
  } = useOrgQuery(`issues/${issueId}/detail`, loadIssueDetail, {
    enabled: canReadIssues,
    showErrorToast: true,
    errorMessage: "שגיאה בטעינת פרטי הליקוי",
  });

  if (!canReadIssues) {
    return (
      <main className="of-dashboard-page">
        <div className="mx-auto max-w-4xl">
          <PageHeader
            title="פרטי ליקוי"
            description="אין הרשאה לצפייה בליקוי זה"
          />
        </div>
      </main>
    );
  }

  if (loading && !detail) {
    return (
      <main className="of-dashboard-page">
        <LoadingState message="טוען פרטי ליקוי..." />
      </main>
    );
  }

  const issue = detail?.issue;
  const events = detail?.events ?? [];
  const projectMismatch =
    issue != null && !issueBelongsToProject(issue, projectId);

  return (
    <main className="of-dashboard-page">
      {isValidating ? <PageLoadingOverlay /> : null}

      <div className="mx-auto max-w-4xl space-y-6">
        <PageHeader
          eyebrow="בקרת איכות"
          title={issue?.title ?? "פרטי ליקוי"}
          description="מעקב מלא על ליקוי בודד - תוכן, סטטוס והיסטוריית אירועים"
          actions={
            <Link
              href={`/projects/${projectId}/issues`}
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
              חזרה לרשימה
            </Link>
          }
        />

        {error && !detail ? (
          <div className="of-card of-card-p8 text-sm text-red-600 dark:text-red-400">
            {error.message}
          </div>
        ) : null}

        {projectMismatch ? (
          <div className="of-card of-card-p8 text-sm text-red-600 dark:text-red-400">
            הליקוי לא שייך לפרויקט זה.
          </div>
        ) : null}

        {issue && !projectMismatch ? (
          <IssueDetailPanel
            issue={issue}
            events={events}
            catalogLink={detail?.catalog_link ?? null}
            actorRole={effectiveRole}
            onIssueUpdated={() => reload()}
          />
        ) : null}
      </div>
    </main>
  );
}
