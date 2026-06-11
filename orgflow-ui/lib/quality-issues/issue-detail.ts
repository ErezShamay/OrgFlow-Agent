import {
  QUALITY_ISSUE_EVENT_TYPE_LABELS_HE,
  QUALITY_ISSUE_STATUS_LABELS_HE,
  type QualityIssue,
  type QualityIssueCatalogLink,
  type QualityIssueEvent,
  type QualityIssueEventType,
  type QualityIssueStatus,
} from "@/lib/quality-issues/types";

export const LIFECYCLE_CLOSURE_EVENT_TYPES: ReadonlySet<QualityIssueEventType> =
  new Set(["REMEDIATION_SUBMITTED", "VERIFIED_CLOSED", "REOPENED"]);

export function formatIssueDateTime(value?: string | null): string {
  if (!value?.trim()) {
    return "-";
  }

  try {
    return new Date(value).toLocaleString("he-IL");
  } catch {
    return value;
  }
}

function statusLabel(status: unknown): string {
  if (
    typeof status === "string" &&
    status in QUALITY_ISSUE_STATUS_LABELS_HE
  ) {
    return QUALITY_ISSUE_STATUS_LABELS_HE[
      status as QualityIssueStatus
    ];
  }

  return typeof status === "string" ? status : "-";
}

export function formatQualityIssueEventSummary(
  event: QualityIssueEvent
): string {
  const payload = event.payload as Record<string, unknown>;
  const label = QUALITY_ISSUE_EVENT_TYPE_LABELS_HE[event.event_type];

  switch (event.event_type) {
    case "DETECTED":
      return label;
    case "LINKED": {
      const source =
        payload.match_source === "auto" ? "אוטומטי" : "ידני";
      return `${label} (${source})`;
    }
    case "REMEDIATION_SUBMITTED":
    case "VERIFIED_CLOSED":
    case "STATUS_CHANGED":
    case "REOPENED":
      return `${label}: ${statusLabel(payload.from_status)} → ${statusLabel(payload.to_status)}`;
    default:
      return label;
  }
}

export function formatQualityIssueEventNotes(
  event: QualityIssueEvent
): string | null {
  const payload = event.payload as Record<string, unknown>;
  const notes = payload.notes ?? payload.reason;

  if (typeof notes === "string" && notes.trim()) {
    return notes.trim();
  }

  return null;
}

export function formatQualityIssueEventDetails(
  event: QualityIssueEvent
): string[] {
  const payload = event.payload as Record<string, unknown>;
  const details: string[] = [];

  const notes = formatQualityIssueEventNotes(event);
  if (notes) {
    details.push(notes);
  }

  if (event.event_type === "REMEDIATION_SUBMITTED") {
    const photoIds = payload.photo_ids;
    if (Array.isArray(photoIds) && photoIds.length > 0) {
      details.push(
        photoIds.length === 1
          ? "תמונת תיקון אחת"
          : `${photoIds.length} תמונות תיקון`
      );
    }
  }

  if (event.event_type === "REOPENED") {
    const count = payload.recurrence_count;
    if (typeof count === "number" && count >= 1) {
      details.push(`ספירת חזרות: ${count}`);
    }

    const previousClosedAt = payload.previous_closed_at;
    if (typeof previousClosedAt === "string" && previousClosedAt.trim()) {
      details.push(`נסגר קודם: ${formatIssueDateTime(previousClosedAt)}`);
    }
  }

  return details;
}

export function sortQualityIssueEvents(
  events: QualityIssueEvent[]
): QualityIssueEvent[] {
  return [...events].sort((left, right) => {
    const leftTime = Date.parse(left.created_at ?? "");
    const rightTime = Date.parse(right.created_at ?? "");

    if (Number.isFinite(leftTime) && Number.isFinite(rightTime)) {
      return rightTime - leftTime;
    }

    return 0;
  });
}

export function issueBelongsToProject(
  issue: QualityIssue,
  projectId: string
): boolean {
  return issue.project_id === projectId;
}

export type IssueDetailField = {
  label: string;
  value: string;
};

export function formatCatalogSectionLabel(
  catalogLink: QualityIssueCatalogLink
): string {
  const parts = [
    catalogLink.category_name_he,
    catalogLink.issue_name_he,
  ].filter((part) => part.trim());

  if (catalogLink.standard_ref?.trim()) {
    parts.push(catalogLink.standard_ref.trim());
  }

  return parts.join(" · ");
}

export function buildIssueDetailFields(
  issue: QualityIssue,
  catalogLink?: QualityIssueCatalogLink | null
): IssueDetailField[] {
  const fields: IssueDetailField[] = [];

  const addField = (label: string, value?: string | null) => {
    if (value?.trim()) {
      fields.push({ label, value: value.trim() });
    }
  };

  addField("מיקום", issue.location);
  addField("מלאכה", issue.trade);
  addField("קיבוץ", issue.group_label_he ?? issue.group_key);

  if (catalogLink) {
    addField("סעיף מפרט", formatCatalogSectionLabel(catalogLink));
    addField("מזהה קטלוג", catalogLink.issue_id);
  } else {
    addField("סעיף מפרט", issue.standard_ref);
    addField("מזהה קטלוג", issue.catalog_issue_id);
  }
  addField("גילוי ראשון", formatIssueDateTime(issue.first_seen_at));
  addField("צפייה אחרונה", formatIssueDateTime(issue.last_seen_at));

  if (issue.closed_at) {
    addField("נסגר", formatIssueDateTime(issue.closed_at));
  }

  if (issue.recurrence_count > 0) {
    fields.push({
      label: "חזרות",
      value: String(issue.recurrence_count),
    });
  }

  if (issue.photo_ids.length > 0) {
    fields.push({
      label: "תמונות",
      value: `${issue.photo_ids.length} תמונות מצורפות`,
    });
  }

  return fields;
}
