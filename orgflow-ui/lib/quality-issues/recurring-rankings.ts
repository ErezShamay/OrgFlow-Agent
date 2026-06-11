import type {
  QualityContractorRecurringRankEntry,
  QualityRecurringIssueRankEntry,
  QualityRecurringRankingsResponse,
} from "@/lib/quality-issues/types";

export function formatRecurringRankingsCaption(
  response: QualityRecurringRankingsResponse
): string {
  if (response.total_recurring === 0) {
    return "אין ליקויים חוזרים בתיק";
  }

  const topIssue = response.issues[0];
  const topContractor = response.contractors[0];

  if (topIssue && topContractor) {
    return `${response.total_recurring} ליקויים חוזרים - הכי לחוץ: ${topContractor.contractor_name} (${topContractor.recurring_issue_count})`;
  }

  return `${response.total_recurring} ליקויים חוזרים בתיק`;
}

export function formatRecurringIssueSubtitle(
  entry: QualityRecurringIssueRankEntry
): string {
  const parts: string[] = [];

  if (entry.project_name?.trim()) {
    parts.push(entry.project_name.trim());
  }

  if (entry.trade?.trim()) {
    parts.push(entry.trade.trim());
  }

  if (entry.contractor_name?.trim()) {
    parts.push(entry.contractor_name.trim());
  }

  return parts.join(" · ") || "ללא פרטים נוספים";
}

export function formatContractorRecurringSubtitle(
  entry: QualityContractorRecurringRankEntry
): string {
  const projectLabel =
    entry.project_count === 1
      ? "פרויקט אחד"
      : `${entry.project_count} פרויקטים`;

  return `${projectLabel} · ${entry.total_recurrence_count} אירועי חזרה`;
}

export function buildProjectIssueHref(
  projectId: string,
  issueId: string
): string {
  return `/projects/${encodeURIComponent(projectId)}/issues/${encodeURIComponent(issueId)}`;
}
