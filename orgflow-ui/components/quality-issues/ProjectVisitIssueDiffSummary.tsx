"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import Button from "@/components/ui/Button";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { hasQCPermission } from "@/lib/quality-issues/permissions";
import {
  formatProjectVisitDiffVisitLabel,
  loadProjectVisitIssueDiffSummaries,
  summarizeProjectVisitDiffRows,
  type ProjectVisitIssueDiffSummaryRow,
} from "@/lib/quality-issues/project-visit-issue-diff";
import { buildVisitIssueDiffBuckets } from "@/lib/quality-issues/visit-issue-diff";
import { useOffline } from "@/providers/OfflineProvider";

type ProjectVisitIssueDiffSummaryProps = {
  projectId: string;
  role: string | null;
};

function VisitDiffSummaryRow({
  row,
}: {
  row: ProjectVisitIssueDiffSummaryRow;
}) {
  const buckets = buildVisitIssueDiffBuckets(row.diff).filter(
    (bucket) => bucket.total > 0
  );

  return (
    <li className="rounded-lg border border-zinc-200/80 bg-white px-4 py-3 dark:border-zinc-800/80 dark:bg-zinc-950/40">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <Link
            href={row.report_href}
            className="font-semibold text-brand hover:underline dark:text-brand-light"
          >
            {formatProjectVisitDiffVisitLabel(row)}
          </Link>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {row.summary_text}
          </p>
        </div>

        {row.status_label_he ? (
          <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200">
            {row.status_label_he}
          </span>
        ) : null}
      </div>

      {buckets.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {buckets.map((bucket) => (
            <span
              key={bucket.category}
              className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
            >
              {bucket.label}: {bucket.total}
            </span>
          ))}
        </div>
      ) : null}
    </li>
  );
}

export default function ProjectVisitIssueDiffSummary({
  projectId,
  role,
}: ProjectVisitIssueDiffSummaryProps) {
  const { isEnabled: fieldReportsEnabled, loading: fieldReportsLoading } =
    useFieldReportModule();
  const { isOnline } = useOffline();
  const canReadIssues = hasQCPermission(role, "quality_issues:read");
  const canReadFieldReports = hasQCPermission(role, "field_reports:read");

  const [rows, setRows] = useState<ProjectVisitIssueDiffSummaryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadSummaries = useCallback(async () => {
    if (
      !canReadIssues
      || !canReadFieldReports
      || !fieldReportsEnabled
      || !isOnline
    ) {
      setLoading(false);
      setError("");
      setRows([]);
      return;
    }

    try {
      setLoading(true);
      setError("");
      const nextRows = await loadProjectVisitIssueDiffSummaries(projectId);
      setRows(nextRows);
    } catch (err: unknown) {
      setRows([]);
      setError(
        err instanceof Error
          ? err.message
          : "טעינת סיכום שינויי הליקויים נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, [
    canReadFieldReports,
    canReadIssues,
    fieldReportsEnabled,
    isOnline,
    projectId,
  ]);

  useEffect(() => {
    if (fieldReportsLoading) {
      return;
    }

    void loadSummaries();
  }, [fieldReportsLoading, loadSummaries]);

  if (
    !canReadIssues
    || !canReadFieldReports
    || !fieldReportsEnabled
    || fieldReportsLoading
  ) {
    return null;
  }

  const aggregate = summarizeProjectVisitDiffRows(rows);
  const aggregateBuckets = aggregate.totals.filter((bucket) => bucket.total > 0);

  return (
    <section className="of-card of-card-p10 of-card-xl mt-10 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="text-zinc-500">מעקב בין ביקורים</p>
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            סיכום שינויי ליקויים
          </h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {aggregate.visit_count > 0
              ? `${aggregate.visit_count} ביקורים אחרונים - ${aggregate.visits_with_changes} עם שינויים`
              : "אין עדיין ביקורים סגורים עם diff ליקויים"}
          </p>
        </div>

        <Link
          href={`/projects/${encodeURIComponent(projectId)}/issues`}
          className="text-sm font-semibold text-brand hover:underline dark:text-brand-light"
        >
          לכל הליקויים
        </Link>
      </div>

      {!isOnline ? (
        <p className="text-sm text-amber-800 dark:text-amber-200">
          סיכום שינויי ליקויים זמין רק במצב מקוון.
        </p>
      ) : null}

      {loading ? (
        <p className="text-sm text-zinc-500">טוען סיכום ביקורים...</p>
      ) : null}

      {!loading && error ? (
        <div className="space-y-2">
          <p className="text-sm text-red-600">{error}</p>
          <Button variant="secondary" size="sm" onClick={() => void loadSummaries()}>
            נסה שוב
          </Button>
        </div>
      ) : null}

      {!loading && !error && aggregateBuckets.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {aggregateBuckets.map((bucket) => (
            <span
              key={bucket.category}
              className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
            >
              {bucket.label}: {bucket.total}
            </span>
          ))}
        </div>
      ) : null}

      {!loading && !error && rows.length > 0 ? (
        <ul className="space-y-3">
          {rows.map((row) => (
            <VisitDiffSummaryRow key={row.report_id} row={row} />
          ))}
        </ul>
      ) : null}

      {!loading && !error && rows.length === 0 && isOnline ? (
        <p className="text-sm text-zinc-500">
          סגירת דוח ביקור תציג כאן ליקויים חדשים, נסגרים וחוזרים.
        </p>
      ) : null}
    </section>
  );
}
