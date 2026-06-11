import type { VisitReportView } from "@/lib/field-reports/visit-report-view";
import type {
  QualityIssueVisitDiffCategory,
  QualityIssueVisitDiffResponse,
} from "@/lib/quality-issues/types";
import { QUALITY_ISSUE_VISIT_DIFF_CATEGORY_LABELS_HE } from "@/lib/quality-issues/types";

export type VisitIssueDiffBucket = {
  category: QualityIssueVisitDiffCategory;
  label: string;
  total: number;
};

export const VISIT_ISSUE_DIFF_BUCKET_ORDER: readonly QualityIssueVisitDiffCategory[] =
  ["new", "closed", "still_open", "recurring"];

export const CLOSED_VISIT_STATUSES_FOR_DIFF = new Set([
  "CLOSED",
  "SENT",
  "PENDING_UPLOAD",
  "LOCKED",
]);

export function isClosedVisitReportStatusForDiff(status: string): boolean {
  return CLOSED_VISIT_STATUSES_FOR_DIFF.has(status.trim().toUpperCase());
}

export function shouldShowVisitIssueDiff(
  report: Pick<VisitReportView, "is_editable" | "project_id" | "status">
): boolean {
  if (report.is_editable) {
    return false;
  }

  if (!report.project_id?.trim()) {
    return false;
  }

  return isClosedVisitReportStatusForDiff(report.status ?? "");
}

export function buildVisitIssueDiffBuckets(
  diff: QualityIssueVisitDiffResponse
): VisitIssueDiffBucket[] {
  return VISIT_ISSUE_DIFF_BUCKET_ORDER.map((category) => ({
    category,
    label: QUALITY_ISSUE_VISIT_DIFF_CATEGORY_LABELS_HE[category],
    total:
      category === "new"
        ? diff.total_new
        : category === "closed"
          ? diff.total_closed
          : category === "still_open"
            ? diff.total_still_open
            : diff.total_recurring,
  }));
}

export function visitIssueDiffHasChanges(
  diff: QualityIssueVisitDiffResponse
): boolean {
  return (
    diff.total_new > 0
    || diff.total_closed > 0
    || diff.total_still_open > 0
    || diff.total_recurring > 0
  );
}

export function formatVisitIssueDiffSummary(
  diff: QualityIssueVisitDiffResponse
): string {
  const parts = buildVisitIssueDiffBuckets(diff)
    .filter((bucket) => bucket.total > 0)
    .map((bucket) => `${bucket.total} ${bucket.label}`);

  return parts.length > 0 ? parts.join(" · ") : "אין שינויי ליקויים בביקור זה";
}

export function buildIssueDetailHref(
  projectId: string,
  issueId: string
): string {
  return `/projects/${encodeURIComponent(projectId)}/issues/${encodeURIComponent(issueId)}`;
}
