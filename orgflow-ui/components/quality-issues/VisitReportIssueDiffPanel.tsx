"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import {
  severityBadgeVariant,
  statusBadgeVariant,
} from "@/components/quality-issues/IssuesTable";
import { getProjectVisitIssueDiff } from "@/lib/quality-issues/api";
import {
  QUALITY_ISSUE_SEVERITY_LABELS_HE,
  QUALITY_ISSUE_STATUS_LABELS_HE,
  QUALITY_ISSUE_VISIT_DIFF_CATEGORY_LABELS_HE,
  type QualityIssueVisitDiffCategory,
  type QualityIssueVisitDiffEntry,
  type QualityIssueVisitDiffResponse,
} from "@/lib/quality-issues/types";
import {
  VISIT_ISSUE_DIFF_BUCKET_ORDER,
  buildIssueDetailHref,
  buildVisitIssueDiffBuckets,
  formatVisitIssueDiffSummary,
  visitIssueDiffHasChanges,
} from "@/lib/quality-issues/visit-issue-diff";

type VisitReportIssueDiffPanelProps = {
  projectId: string;
  reportId: string;
  isOnline: boolean;
};

function diffCategoryBadgeVariant(
  category: QualityIssueVisitDiffCategory
): "success" | "warning" | "info" | "danger" | "neutral" {
  switch (category) {
    case "closed":
      return "success";
    case "new":
      return "info";
    case "still_open":
      return "warning";
    case "recurring":
      return "danger";
    default:
      return "neutral";
  }
}

function DiffIssueRow({
  entry,
  projectId,
}: {
  entry: QualityIssueVisitDiffEntry;
  projectId: string;
}) {
  const issue = entry.issue;

  return (
    <li className="rounded-lg border border-zinc-200/80 bg-white px-3 py-3 dark:border-zinc-800/80 dark:bg-zinc-950/40">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 space-y-1">
          <Link
            href={buildIssueDetailHref(projectId, issue.id)}
            className="font-semibold text-brand hover:underline dark:text-brand-light"
          >
            {issue.title}
          </Link>
          <p className="text-xs text-zinc-500">
            {[issue.location, issue.trade].filter(Boolean).join(" · ") || "-"}
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Badge variant={diffCategoryBadgeVariant(entry.category)}>
            {QUALITY_ISSUE_VISIT_DIFF_CATEGORY_LABELS_HE[entry.category]}
          </Badge>
          <Badge variant={statusBadgeVariant(issue.status)}>
            {QUALITY_ISSUE_STATUS_LABELS_HE[issue.status]}
          </Badge>
          <Badge variant={severityBadgeVariant(issue.severity)}>
            {QUALITY_ISSUE_SEVERITY_LABELS_HE[issue.severity]}
          </Badge>
        </div>
      </div>
    </li>
  );
}

function DiffBucketSection({
  category,
  entries,
  projectId,
}: {
  category: QualityIssueVisitDiffCategory;
  entries: QualityIssueVisitDiffEntry[];
  projectId: string;
}) {
  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">
        {QUALITY_ISSUE_VISIT_DIFF_CATEGORY_LABELS_HE[category]} ({entries.length})
      </h3>
      <ul className="space-y-2">
        {entries.map((entry) => (
          <DiffIssueRow
            key={`${category}-${entry.issue.id}`}
            entry={entry}
            projectId={projectId}
          />
        ))}
      </ul>
    </section>
  );
}

function getBucketEntries(
  diff: QualityIssueVisitDiffResponse,
  category: QualityIssueVisitDiffCategory
): QualityIssueVisitDiffEntry[] {
  switch (category) {
    case "new":
      return diff.new;
    case "closed":
      return diff.closed;
    case "still_open":
      return diff.still_open;
    case "recurring":
      return diff.recurring;
    default:
      return [];
  }
}

export default function VisitReportIssueDiffPanel({
  projectId,
  reportId,
  isOnline,
}: VisitReportIssueDiffPanelProps) {
  const [diff, setDiff] = useState<QualityIssueVisitDiffResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDiff = async () => {
    if (!isOnline) {
      setLoading(false);
      setError("");
      setDiff(null);
      return;
    }

    try {
      setLoading(true);
      setError("");
      const response = await getProjectVisitIssueDiff(projectId, reportId);
      setDiff(response);
    } catch (err: unknown) {
      setDiff(null);
      setError(
        err instanceof Error
          ? err.message
          : "טעינת שינויי הליקויים נכשלה"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadDiff();
  }, [projectId, reportId, isOnline]);

  return (
    <section className="space-y-4 rounded-xl border border-zinc-200 bg-white/80 p-4 dark:border-zinc-800 dark:bg-zinc-900/40 md:p-5">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          שינויי ליקויים בביקור זה
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          השוואה ל-registry - ליקויים חדשים, נסגרו, עדיין פתוחים או חוזרים.
        </p>
      </div>

      {!isOnline ? (
        <p className="text-sm text-amber-800 dark:text-amber-200">
          שינויי ליקויים זמינים רק במצב מקוון.
        </p>
      ) : null}

      {loading ? (
        <p className="text-sm text-zinc-500">טוען שינויי ליקויים...</p>
      ) : null}

      {!loading && error ? (
        <div className="space-y-2">
          <p className="text-sm text-red-600">{error}</p>
          <Button variant="secondary" size="sm" onClick={() => void loadDiff()}>
            נסה שוב
          </Button>
        </div>
      ) : null}

      {!loading && !error && diff ? (
        <div className="space-y-4">
          <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            {formatVisitIssueDiffSummary(diff)}
          </p>

          <div className="flex flex-wrap gap-2">
            {buildVisitIssueDiffBuckets(diff).map((bucket) => (
              <span
                key={bucket.category}
                className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
              >
                {bucket.label}: {bucket.total}
              </span>
            ))}
          </div>

          {visitIssueDiffHasChanges(diff) ? (
            <div className="space-y-5">
              {VISIT_ISSUE_DIFF_BUCKET_ORDER.map((category) => (
                <DiffBucketSection
                  key={category}
                  category={category}
                  entries={getBucketEntries(diff, category)}
                  projectId={projectId}
                />
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500">
              לא נרשמו שינויי ליקויים בביקור זה.
            </p>
          )}
        </div>
      ) : null}
    </section>
  );
}
