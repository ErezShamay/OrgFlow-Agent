import type { ProjectFieldVisitListItem } from "@/lib/field-reports/project-visits";
import { listProjectFieldVisitReports } from "@/lib/field-reports/project-visits";
import { fieldReportDetailPath } from "@/lib/field-reports/routes";
import { getProjectVisitIssueDiff } from "@/lib/quality-issues/api";
import type { QualityIssueVisitDiffResponse } from "@/lib/quality-issues/types";
import {
  buildVisitIssueDiffBuckets,
  formatVisitIssueDiffSummary,
  isClosedVisitReportStatusForDiff,
  visitIssueDiffHasChanges,
  type VisitIssueDiffBucket,
} from "@/lib/quality-issues/visit-issue-diff";

export const PROJECT_VISIT_DIFF_SUMMARY_LIMIT = 5;

export type ProjectVisitIssueDiffSummaryRow = {
  report_id: string;
  visit_date: string;
  visit_type_label_he: string;
  status: string;
  status_label_he?: string;
  diff: QualityIssueVisitDiffResponse;
  summary_text: string;
  has_changes: boolean;
  report_href: string;
};

export function selectRecentClosedVisitsForDiff(
  visits: readonly ProjectFieldVisitListItem[],
  limit: number = PROJECT_VISIT_DIFF_SUMMARY_LIMIT
): ProjectFieldVisitListItem[] {
  return [...visits]
    .filter((visit) => isClosedVisitReportStatusForDiff(visit.status))
    .sort(
      (left, right) =>
        new Date(right.visit_date).getTime()
        - new Date(left.visit_date).getTime()
    )
    .slice(0, Math.max(limit, 0));
}

export function buildProjectVisitIssueDiffSummaryRow(
  visit: ProjectFieldVisitListItem,
  diff: QualityIssueVisitDiffResponse
): ProjectVisitIssueDiffSummaryRow {
  return {
    report_id: visit.id,
    visit_date: visit.visit_date,
    visit_type_label_he: visit.visit_type_label_he,
    status: visit.status,
    status_label_he: visit.status_label_he,
    diff,
    summary_text: formatVisitIssueDiffSummary(diff),
    has_changes: visitIssueDiffHasChanges(diff),
    report_href: fieldReportDetailPath(visit.id),
  };
}

export function formatProjectVisitDiffVisitLabel(
  row: Pick<
    ProjectVisitIssueDiffSummaryRow,
    "visit_date" | "visit_type_label_he"
  >
): string {
  const dateLabel = formatVisitDateLabel(row.visit_date);
  return `${dateLabel} · ${row.visit_type_label_he}`;
}

export function formatVisitDateLabel(visitDate: string): string {
  try {
    return new Date(visitDate).toLocaleDateString("he-IL");
  } catch {
    return visitDate;
  }
}

export function summarizeProjectVisitDiffRows(
  rows: readonly ProjectVisitIssueDiffSummaryRow[]
): {
  visit_count: number;
  visits_with_changes: number;
  totals: VisitIssueDiffBucket[];
} {
  const totals = {
    new: 0,
    closed: 0,
    still_open: 0,
    recurring: 0,
  };

  for (const row of rows) {
    totals.new += row.diff.total_new;
    totals.closed += row.diff.total_closed;
    totals.still_open += row.diff.total_still_open;
    totals.recurring += row.diff.total_recurring;
  }

  return {
    visit_count: rows.length,
    visits_with_changes: rows.filter((row) => row.has_changes).length,
    totals: buildVisitIssueDiffBuckets({
      project_id: "",
      report_id: "",
      new: [],
      closed: [],
      still_open: [],
      recurring: [],
      total_new: totals.new,
      total_closed: totals.closed,
      total_still_open: totals.still_open,
      total_recurring: totals.recurring,
    }),
  };
}

export async function loadProjectVisitIssueDiffSummaries(
  projectId: string,
  options: { limit?: number } = {}
): Promise<ProjectVisitIssueDiffSummaryRow[]> {
  const limit = options.limit ?? PROJECT_VISIT_DIFF_SUMMARY_LIMIT;
  const { reports } = await listProjectFieldVisitReports(projectId);
  const visits = selectRecentClosedVisitsForDiff(reports, limit);

  const rows: ProjectVisitIssueDiffSummaryRow[] = [];

  for (const visit of visits) {
    const diff = await getProjectVisitIssueDiff(projectId, visit.id);
    rows.push(buildProjectVisitIssueDiffSummaryRow(visit, diff));
  }

  return rows;
}
