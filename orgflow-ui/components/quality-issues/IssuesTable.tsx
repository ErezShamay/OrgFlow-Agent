"use client";

import Link from "next/link";

import Badge from "@/components/ui/Badge";
import {
  QUALITY_ISSUE_SEVERITY_LABELS_HE,
  QUALITY_ISSUE_STATUS_LABELS_HE,
  type QualityIssue,
  type QualityIssueSeverity,
  type QualityIssueStatus,
} from "@/lib/quality-issues/types";

export type IssuesTableProps = {
  issues: QualityIssue[];
  projectId?: string;
  projectNames?: Record<string, string>;
  showProjectColumn?: boolean;
  total?: number;
  className?: string;
};

export function formatIssueDate(value?: string | null): string {
  if (!value?.trim()) {
    return "-";
  }

  try {
    return new Date(value).toLocaleDateString("he-IL");
  } catch {
    return value;
  }
}

export function severityBadgeVariant(
  severity: QualityIssueSeverity
): "danger" | "warning" | "info" | "neutral" {
  switch (severity) {
    case "CRITICAL":
      return "danger";
    case "HIGH":
      return "warning";
    case "MEDIUM":
      return "info";
    default:
      return "neutral";
  }
}

export function statusBadgeVariant(
  status: QualityIssueStatus
): "success" | "warning" | "info" | "neutral" {
  switch (status) {
    case "CLOSED":
      return "success";
    case "OPEN":
    case "REOPENED":
      return "warning";
    case "IN_REMEDIATION":
    case "PENDING_VERIFICATION":
      return "info";
    default:
      return "neutral";
  }
}

export function formatIssuesTableSummary(
  shownCount: number,
  total?: number
): string {
  if (total == null || total === shownCount) {
    return `${shownCount} ליקויים`;
  }

  return `מציג ${shownCount} מתוך ${total} ליקויים`;
}

export function formatIssueLocation(value?: string | null): string {
  return value?.trim() || "-";
}

export function formatIssueTrade(value?: string | null): string {
  return value?.trim() || "-";
}

export function formatIssuePhotoCount(photoIds: string[]): string {
  return photoIds.length > 0 ? `${photoIds.length} תמונות` : "-";
}

export function issueHasPhotos(photoIds: string[]): boolean {
  return photoIds.length > 0;
}

export const ISSUES_TABLE_COLUMN_LABELS = [
  "ליקוי",
  "סטטוס",
  "חומרה",
  "מיקום",
  "מלאכה",
  "גילוי ראשון",
  "תמונות",
] as const;

export type IssueTableRowModel = {
  id: string;
  href: string;
  projectId: string;
  projectLabel: string | null;
  title: string;
  description: string | null;
  statusLabel: string;
  statusVariant: ReturnType<typeof statusBadgeVariant>;
  severityLabel: string;
  severityVariant: ReturnType<typeof severityBadgeVariant>;
  location: string;
  trade: string;
  firstSeenAt: string;
  photoCountLabel: string;
  photoCount: number;
  hasPhotos: boolean;
};

export function buildIssueTableRow(
  issue: QualityIssue,
  options: {
    projectId?: string;
    projectNames?: Record<string, string>;
  } = {}
): IssueTableRowModel {
  const resolvedProjectId = options.projectId ?? issue.project_id;
  const projectLabel =
    options.projectNames?.[resolvedProjectId]?.trim() || null;

  return {
    id: issue.id,
    projectId: resolvedProjectId,
    projectLabel,
    href: `/projects/${encodeURIComponent(resolvedProjectId)}/issues/${encodeURIComponent(issue.id)}`,
    title: issue.title,
    description: issue.description?.trim() || null,
    statusLabel: QUALITY_ISSUE_STATUS_LABELS_HE[issue.status],
    statusVariant: statusBadgeVariant(issue.status),
    severityLabel: QUALITY_ISSUE_SEVERITY_LABELS_HE[issue.severity],
    severityVariant: severityBadgeVariant(issue.severity),
    location: formatIssueLocation(issue.location),
    trade: formatIssueTrade(issue.trade),
    firstSeenAt: formatIssueDate(issue.first_seen_at),
    photoCountLabel: formatIssuePhotoCount(issue.photo_ids),
    photoCount: issue.photo_ids.length,
    hasPhotos: issueHasPhotos(issue.photo_ids),
  };
}

export function buildIssuesTableRows(
  issues: QualityIssue[],
  options: {
    projectId?: string;
    projectNames?: Record<string, string>;
  } = {}
): IssueTableRowModel[] {
  return issues.map((issue) => buildIssueTableRow(issue, options));
}

function IssueRow({
  row,
  showProjectColumn,
}: {
  row: IssueTableRowModel;
  showProjectColumn: boolean;
}) {
  return (
    <tr className="border-b border-zinc-200/80 dark:border-zinc-800/80">
      {showProjectColumn ? (
        <td className="px-4 py-4 align-top text-sm text-zinc-600 dark:text-zinc-400">
          {row.projectLabel ?? row.projectId}
        </td>
      ) : null}
      <td className="px-4 py-4 align-top">
        <Link
          href={row.href}
          className="font-semibold text-brand hover:underline dark:text-brand-light"
        >
          {row.title}
        </Link>
        {row.description ? (
          <p className="mt-1 max-w-md text-sm text-zinc-500 line-clamp-2">
            {row.description}
          </p>
        ) : null}
      </td>

      <td className="px-4 py-4 align-top">
        <Badge variant={row.statusVariant}>{row.statusLabel}</Badge>
      </td>

      <td className="px-4 py-4 align-top">
        <Badge variant={row.severityVariant}>{row.severityLabel}</Badge>
      </td>

      <td className="px-4 py-4 align-top text-sm text-zinc-600 dark:text-zinc-400">
        {row.location}
      </td>

      <td className="px-4 py-4 align-top text-sm text-zinc-600 dark:text-zinc-400">
        {row.trade}
      </td>

      <td className="px-4 py-4 align-top text-sm text-zinc-600 dark:text-zinc-400">
        {row.firstSeenAt}
      </td>

      <td className="px-4 py-4 align-top text-sm text-zinc-500">
        {row.hasPhotos ? (
          <span
            className="inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
            title="תמונות מדוח השטח"
          >
            <span aria-hidden className="text-zinc-400">
              ◉
            </span>
            {row.photoCountLabel}
          </span>
        ) : (
          row.photoCountLabel
        )}
      </td>
    </tr>
  );
}

export default function IssuesTable({
  issues,
  projectId,
  projectNames,
  showProjectColumn = false,
  total,
  className = "",
}: IssuesTableProps) {
  if (issues.length === 0) {
    return null;
  }

  const columnLabels = showProjectColumn
    ? (["פרויקט", ...ISSUES_TABLE_COLUMN_LABELS] as const)
    : ISSUES_TABLE_COLUMN_LABELS;

  return (
    <div className={`space-y-4 ${className}`}>
      <p className="text-sm text-zinc-500">
        {formatIssuesTableSummary(issues.length, total)}
      </p>

      <div className="of-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-right">
            <thead className="bg-zinc-50 text-sm text-zinc-500 dark:bg-zinc-900/60">
              <tr>
                {columnLabels.map((label) => (
                  <th key={label} className="px-4 py-3 font-semibold">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {buildIssuesTableRows(issues, { projectId, projectNames }).map(
                (row) => (
                  <IssueRow
                    key={row.id}
                    row={row}
                    showProjectColumn={showProjectColumn}
                  />
                )
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
