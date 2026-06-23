"use client";

import Link from "next/link";
import { useCallback } from "react";

import ProjectSupervisionKpiRow from "@/components/projects/ProjectSupervisionKpiRow";
import Badge from "@/components/ui/Badge";
import LoadingState from "@/components/ui/LoadingState";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import {
  fetchProjectSupervisionTradeDetail,
  projectApartmentPortalPath,
} from "@/lib/projects/supervision-dashboard";
import type { SupervisionTradeDetail } from "@/lib/projects/supervision-dashboard-types";

type ProjectTradeDetailViewProps = {
  projectId: string;
  tradeKey: string;
};

function tradeStatusBadgeVariant(
  status: string
): "success" | "warning" | "danger" | "neutral" {
  switch (status) {
    case "completed":
      return "success";
    case "in_treatment":
      return "warning";
    case "with_defects":
      return "danger";
    default:
      return "neutral";
  }
}

export default function ProjectTradeDetailView({
  projectId,
  tradeKey,
}: ProjectTradeDetailViewProps) {
  const loadDetail = useCallback(async () => {
    return fetchProjectSupervisionTradeDetail(projectId, tradeKey);
  }, [projectId, tradeKey]);

  const { data, loading, error } = useOrgQuery(
    `projects/${projectId}/supervision-trades/${tradeKey}`,
    loadDetail,
    { showErrorToast: false }
  );

  if (loading && !data) {
    return <LoadingState message="טוען פירוט מלאכה..." />;
  }

  if (error && !data) {
    return (
      <section className="of-card of-card-p8 text-sm text-red-600 dark:text-red-400">
        {error.message}
      </section>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <TradeDetailContent projectId={projectId} detail={data} />
  );
}

function TradeDetailContent({
  projectId,
  detail,
}: {
  projectId: string;
  detail: SupervisionTradeDetail;
}) {
  return (
    <div className="space-y-8" dir="rtl">
      <header className="space-y-3">
        <Link
          href={`/projects/${encodeURIComponent(projectId)}`}
          className="text-sm font-medium text-brand hover:underline dark:text-brand-light"
        >
          חזרה לדשבורד הפרויקט
        </Link>
        <h1 className="of-page-title">{detail.label_he}</h1>
        <p className="of-page-desc">
          {detail.project_name} — פירוט פריטי צ&apos;קליסט לפי דירה
        </p>
      </header>

      <ProjectSupervisionKpiRow kpis={detail.kpis} />

      <section className="of-card of-card-p6 shadow-sm">
        <h2 className="mb-4 text-xl font-bold">פריטים לפי דירה</h2>

        {detail.items.length === 0 ? (
          <p className="text-sm text-zinc-500">אין פריטים למלאכה זו.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-200 text-right dark:border-zinc-700">
                  <th className="px-3 py-3 font-semibold">דירה / אזור</th>
                  <th className="px-3 py-3 font-semibold">פריט</th>
                  <th className="px-3 py-3 font-semibold">סטטוס</th>
                  <th className="px-3 py-3 font-semibold">ליקוי</th>
                </tr>
              </thead>
              <tbody>
                {detail.items.map((item, index) => (
                  <tr
                    key={`${item.scope_label_he}-${item.item_name_he}-${index}`}
                    className="border-b border-zinc-100 dark:border-zinc-800"
                  >
                    <td className="px-3 py-3">
                      {item.apartment_id ? (
                        <Link
                          href={projectApartmentPortalPath(
                            projectId,
                            item.apartment_id
                          )}
                          className="font-medium text-brand hover:underline dark:text-brand-light"
                        >
                          {item.scope_label_he}
                        </Link>
                      ) : (
                        item.scope_label_he
                      )}
                    </td>
                    <td className="px-3 py-3">{item.item_name_he}</td>
                    <td className="px-3 py-3">
                      <Badge variant={tradeStatusBadgeVariant(item.status)}>
                        {item.display_status_he}
                      </Badge>
                    </td>
                    <td className="px-3 py-3">
                      {item.linked_issue_id ? (
                        <Link
                          href={`/issues/${encodeURIComponent(item.linked_issue_id)}`}
                          className="text-brand hover:underline dark:text-brand-light"
                        >
                          צפייה בליקוי
                        </Link>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
