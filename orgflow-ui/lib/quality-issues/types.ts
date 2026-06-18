/**
 * QC Spec 0.1–0.2 - QualityIssue + quality_issue_events (mirrors backend).
 * See docs/PRODUCT-SPEC-LOCKED.md §5.
 */

export const QUALITY_ISSUE_SEVERITIES = [
  "CRITICAL",
  "HIGH",
  "MEDIUM",
  "LOW",
] as const;

export type QualityIssueSeverity = (typeof QUALITY_ISSUE_SEVERITIES)[number];

export const QUALITY_ISSUE_STATUSES = [
  "OPEN",
  "IN_REMEDIATION",
  "PENDING_VERIFICATION",
  "CLOSED",
  "REOPENED",
] as const;

export type QualityIssueStatus = (typeof QUALITY_ISSUE_STATUSES)[number];

export const ISSUE_VISIBILITIES = ["DRAFT", "PUBLISHED"] as const;

export type IssueVisibility = (typeof ISSUE_VISIBILITIES)[number];

export const DEFAULT_ISSUE_VISIBILITY: IssueVisibility = "DRAFT";

export function isVisibleToResident(
  visibility: IssueVisibility | string | null | undefined
): boolean {
  if (!visibility) {
    return true;
  }
  return String(visibility).trim().toUpperCase() === "PUBLISHED";
}

export const QUALITY_ISSUE_SEVERITY_LABELS_HE: Record<
  QualityIssueSeverity,
  string
> = {
  CRITICAL: "קריטי",
  HIGH: "גבוה",
  MEDIUM: "בינוני",
  LOW: "נמוך",
};

export const QUALITY_ISSUE_STATUS_LABELS_HE: Record<
  QualityIssueStatus,
  string
> = {
  OPEN: "פתוח",
  IN_REMEDIATION: "בטיפול",
  PENDING_VERIFICATION: "ממתין לאימות",
  CLOSED: "סגור",
  REOPENED: "נפתח מחדש",
};

export const CATALOG_SEVERITY_TO_REGISTRY: Record<
  string,
  QualityIssueSeverity
> = {
  critical: "CRITICAL",
  high: "HIGH",
  medium: "MEDIUM",
  low: "LOW",
};

export const DEFAULT_QUALITY_ISSUE_SEVERITY: QualityIssueSeverity = "MEDIUM";
export const DEFAULT_QUALITY_ISSUE_STATUS: QualityIssueStatus = "OPEN";

export type QualityIssue = {
  id: string;
  organization_id: string;
  project_id: string;

  title: string;
  description?: string | null;
  location?: string | null;
  trade?: string | null;
  group_key?: string | null;
  group_label_he?: string | null;
  standard_ref?: string | null;

  severity: QualityIssueSeverity;
  status: QualityIssueStatus;
  visibility: IssueVisibility;

  catalog_issue_id?: string | null;

  first_seen_report_id: string;
  first_seen_line_id?: string | null;
  first_seen_at: string;
  last_seen_report_id: string;
  last_seen_line_id?: string | null;
  last_seen_at: string;
  closed_at?: string | null;
  closed_by?: string | null;
  recurrence_count: number;

  photo_ids: string[];
  materialization_key: string;

  created_at?: string | null;
  updated_at?: string | null;
};

export function normalizeCatalogSeverity(
  value: string | null | undefined
): QualityIssueSeverity | null {
  const raw = value?.trim().toLowerCase();
  if (!raw) {
    return null;
  }
  return CATALOG_SEVERITY_TO_REGISTRY[raw] ?? null;
}

export function buildMaterializationKey(
  reportId: string,
  lineId: string
): string {
  return `${reportId}:${lineId}`;
}

export function buildMatchKey(parts: {
  location?: string | null;
  trade?: string | null;
  group_key?: string | null;
}): string {
  const normalize = (value: string | null | undefined): string => {
    if (!value?.trim()) {
      return "";
    }
    return value.trim().toLowerCase().replace(/\s+/g, " ");
  };

  return [
    normalize(parts.location),
    normalize(parts.trade),
    normalize(parts.group_key),
  ].join("|");
}

export const QUALITY_ISSUE_EVENT_TYPES = [
  "DETECTED",
  "CREATED_FROM_FIELD",
  "LINKED",
  "REMEDIATION_SUBMITTED",
  "VERIFIED_CLOSED",
  "REOPENED",
  "STATUS_CHANGED",
] as const;

export type QualityIssueEventType = (typeof QUALITY_ISSUE_EVENT_TYPES)[number];

export const QUALITY_ISSUE_EVENT_TYPE_LABELS_HE: Record<
  QualityIssueEventType,
  string
> = {
  DETECTED: "התגלות",
  CREATED_FROM_FIELD: "נוצר משטח",
  LINKED: "קישור לליקוי קיים",
  REMEDIATION_SUBMITTED: "הוגש תיקון",
  VERIFIED_CLOSED: "אושר ונסגר",
  REOPENED: "נפתח מחדש",
  STATUS_CHANGED: "שינוי סטטוס",
};

export const EVENT_TYPES_REQUIRING_ACTOR: ReadonlySet<QualityIssueEventType> =
  new Set(["REMEDIATION_SUBMITTED", "VERIFIED_CLOSED", "STATUS_CHANGED"]);

export const EVENT_TYPES_REQUIRING_REPORT: ReadonlySet<QualityIssueEventType> =
  new Set(["DETECTED", "CREATED_FROM_FIELD", "LINKED", "VERIFIED_CLOSED", "REOPENED"]);

export type DetectedEventPayload = {
  materialization_key: string;
  severity: QualityIssueSeverity;
  title: string;
  catalog_issue_id?: string | null;
  location?: string | null;
  trade?: string | null;
  group_key?: string | null;
};

export type LinkedEventPayload = {
  match_key?: string | null;
  match_source?: "auto" | "manual";
  previous_last_seen_at?: string | null;
};

export type RemediationSubmittedEventPayload = {
  from_status: QualityIssueStatus;
  to_status: QualityIssueStatus;
  photo_ids?: string[];
  notes?: string | null;
};

export type VerifiedClosedEventPayload = {
  from_status: QualityIssueStatus;
  to_status: "CLOSED";
  notes?: string | null;
};

export type ReopenedEventPayload = {
  from_status: "CLOSED";
  to_status: "REOPENED";
  recurrence_count: number;
  previous_closed_at?: string | null;
  match_key?: string | null;
};

export type StatusChangedEventPayload = {
  from_status: QualityIssueStatus;
  to_status: QualityIssueStatus;
  reason?: string | null;
};

export type QualityIssueEventPayloadByType = {
  DETECTED: DetectedEventPayload;
  LINKED: LinkedEventPayload;
  REMEDIATION_SUBMITTED: RemediationSubmittedEventPayload;
  VERIFIED_CLOSED: VerifiedClosedEventPayload;
  REOPENED: ReopenedEventPayload;
  STATUS_CHANGED: StatusChangedEventPayload;
};

export type QualityIssueEvent = {
  id: string;
  issue_id: string;
  event_type: QualityIssueEventType;
  report_id?: string | null;
  line_id?: string | null;
  actor_id?: string | null;
  payload: QualityIssueEventPayloadByType[QualityIssueEventType];
  created_at?: string | null;
};

export function preferredEventTypeForTransition(
  fromStatus: QualityIssueStatus | null | undefined,
  toStatus: QualityIssueStatus
): QualityIssueEventType {
  if (!fromStatus && toStatus === "OPEN") {
    return "DETECTED";
  }
  if (fromStatus === "CLOSED" && toStatus === "REOPENED") {
    return "REOPENED";
  }
  if (
    fromStatus === "IN_REMEDIATION" &&
    toStatus === "PENDING_VERIFICATION"
  ) {
    return "REMEDIATION_SUBMITTED";
  }
  if (toStatus === "CLOSED") {
    return "VERIFIED_CLOSED";
  }
  return "STATUS_CHANGED";
}

/** Numeric rank for severity sorting (higher = more severe). */
export const QUALITY_ISSUE_SEVERITY_RANK: Record<
  QualityIssueSeverity,
  number
> = {
  CRITICAL: 4,
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1,
};

export function severityRank(severity: QualityIssueSeverity): number {
  return QUALITY_ISSUE_SEVERITY_RANK[severity];
}

/** Positive when `a` is more severe than `b`. */
export function compareSeverity(
  a: QualityIssueSeverity,
  b: QualityIssueSeverity
): number {
  return severityRank(a) - severityRank(b);
}

export function isTerminalIssueStatus(status: QualityIssueStatus): boolean {
  return status === "CLOSED";
}

export const QUALITY_ISSUE_STATUS_TRANSITIONS: Record<
  QualityIssueStatus,
  readonly QualityIssueStatus[]
> = {
  OPEN: ["IN_REMEDIATION", "CLOSED"],
  IN_REMEDIATION: ["PENDING_VERIFICATION"],
  PENDING_VERIFICATION: ["CLOSED", "OPEN"],
  CLOSED: ["REOPENED"],
  REOPENED: ["IN_REMEDIATION", "CLOSED"],
};

export function isValidStatusTransition(
  current: QualityIssueStatus,
  target: QualityIssueStatus
): boolean {
  if (current === target) {
    return true;
  }
  return QUALITY_ISSUE_STATUS_TRANSITIONS[current]?.includes(target) ?? false;
}

export function resolveIssueSeverity(options: {
  catalogSeverity?: string | null;
  rowSeverity?: string | null;
}): QualityIssueSeverity {
  for (const candidate of [options.catalogSeverity, options.rowSeverity]) {
    const resolved = normalizeCatalogSeverity(candidate);
    if (resolved) {
      return resolved;
    }
  }
  return DEFAULT_QUALITY_ISSUE_SEVERITY;
}

export function deriveIssueTitle(options: {
  description?: string | null;
  location?: string | null;
  trade?: string | null;
  catalogIssueName?: string | null;
  maxDescriptionLen?: number;
}): string {
  const maxLen = options.maxDescriptionLen ?? 80;
  const catalogName = options.catalogIssueName?.trim();
  if (catalogName) {
    return catalogName;
  }

  const desc = (options.description ?? "").trim();
  if (desc) {
    if (desc.length <= maxLen) {
      return desc;
    }
    return `${desc.slice(0, maxLen - 1).trimEnd()}…`;
  }

  const location = (options.location ?? "").trim();
  const trade = (options.trade ?? "").trim();
  if (location && trade) {
    return `${location} - ${trade}`;
  }
  if (location) {
    return location;
  }
  if (trade) {
    return trade;
  }

  return "ליקוי ללא תיאור";
}

export function findingRowQualifiesForMaterialization(options: {
  description?: string | null;
  catalogIssueId?: string | null;
  photoIds?: string[] | null;
}): boolean {
  if (options.catalogIssueId?.trim()) {
    return true;
  }
  if ((options.description ?? "").trim()) {
    return true;
  }
  return Boolean(options.photoIds?.length);
}

/** POST /projects/{id}/issues */
export type QualityIssueCreateRequest = {
  title: string;
  description?: string | null;
  location?: string | null;
  trade?: string | null;
  group_key?: string | null;
  group_label_he?: string | null;
  standard_ref?: string | null;
  severity?: QualityIssueSeverity;
  visibility?: IssueVisibility;
  catalog_issue_id?: string | null;
  first_seen_report_id: string;
  first_seen_line_id?: string | null;
  first_seen_at: string;
  last_seen_report_id?: string | null;
  last_seen_line_id?: string | null;
  last_seen_at?: string | null;
  photo_ids?: string[];
  materialization_key: string;
};

/** PATCH /issues/{id} */
export type QualityIssueUpdateRequest = {
  title?: string;
  description?: string | null;
  location?: string | null;
  trade?: string | null;
  group_key?: string | null;
  group_label_he?: string | null;
  standard_ref?: string | null;
  severity?: QualityIssueSeverity;
  status?: QualityIssueStatus;
  catalog_issue_id?: string | null;
  last_seen_report_id?: string | null;
  last_seen_line_id?: string | null;
  last_seen_at?: string | null;
  closed_at?: string | null;
  closed_by?: string | null;
  photo_ids?: string[];
  notes?: string | null;
};

/** Focused status transition payload (verify / remediate flows). */
export type QualityIssueStatusUpdateRequest = {
  status: QualityIssueStatus;
  report_id?: string | null;
  line_id?: string | null;
  notes?: string | null;
  photo_ids?: string[];
};

/** GET /projects/{id}/issues query parameters. */
export type QualityIssueListQuery = {
  status?: QualityIssueStatus[];
  severity?: QualityIssueSeverity[];
  trade?: string | null;
  search?: string | null;
  limit?: number;
  offset?: number;
};

export const DEFAULT_QUALITY_ISSUE_LIST_LIMIT = 50;
export const MAX_QUALITY_ISSUE_LIST_LIMIT = 200;

export const DEFAULT_QUALITY_ISSUE_LIST_QUERY: Required<
  Pick<QualityIssueListQuery, "limit" | "offset">
> = {
  limit: DEFAULT_QUALITY_ISSUE_LIST_LIMIT,
  offset: 0,
};

/** GET /projects/{id}/issues */
export type QualityIssueListResponse = {
  project_id: string;
  total: number;
  limit: number;
  offset: number;
  items: QualityIssue[];
};

/** GET /issues - cross-project list */
export type QualityIssueOrgListResponse = {
  organization_id: string;
  total: number;
  limit: number;
  offset: number;
  items: QualityIssue[];
};

/** GET /projects/{id}/issues/open */
export type QualityIssueOpenListResponse = {
  project_id: string;
  total: number;
  items: QualityIssue[];
};

/** POST /projects/{id}/issues/suggest-matches - finding row input */
export type FindingMatchInput = {
  location?: string | null;
  trade?: string | null;
  group_key?: string | null;
  catalog_issue_id?: string | null;
};

export type QualityIssueMatchCandidate = {
  issue: QualityIssue;
  match_key: string;
  score: number;
};

export type QualityIssueSuggestMatchesRequest = FindingMatchInput & {
  limit?: number;
};

/** POST /projects/{id}/issues/suggest-matches */
export type QualityIssueSuggestMatchesResponse = {
  project_id: string;
  match_key: string;
  total: number;
  candidates: QualityIssueMatchCandidate[];
};

/** GET /issues/{id} */
export type QualityIssueDetailResponse = {
  issue: QualityIssue;
  events: QualityIssueEvent[];
  catalog_link: QualityIssueCatalogLink | null;
};

/** GET /portfolio/quality-summary - per-project rollup. */
export type QualityPortfolioProjectSummary = {
  project_id: string;
  project_name?: string | null;
  open_total: number;
  open_critical: number;
  critical_open_over_14_days: number;
  average_open_days?: number | null;
};

export const QUALITY_ISSUE_VISIT_DIFF_CATEGORIES = [
  "new",
  "closed",
  "still_open",
  "recurring",
] as const;

export type QualityIssueVisitDiffCategory =
  (typeof QUALITY_ISSUE_VISIT_DIFF_CATEGORIES)[number];

export const QUALITY_ISSUE_VISIT_DIFF_CATEGORY_LABELS_HE: Record<
  QualityIssueVisitDiffCategory,
  string
> = {
  new: "חדש",
  closed: "נסגר",
  still_open: "עדיין פתוח",
  recurring: "חוזר",
};

/** GET /projects/{id}/visits/{report_id}/issue-diff */
export type QualityIssueVisitDiffEntry = {
  issue: QualityIssue;
  line_id?: string | null;
  category: QualityIssueVisitDiffCategory;
};

export type QualityIssueVisitDiffResponse = {
  project_id: string;
  report_id: string;
  new: QualityIssueVisitDiffEntry[];
  closed: QualityIssueVisitDiffEntry[];
  still_open: QualityIssueVisitDiffEntry[];
  recurring: QualityIssueVisitDiffEntry[];
  total_new: number;
  total_closed: number;
  total_still_open: number;
  total_recurring: number;
};

/** GET /portfolio/quality-summary */
export type QualityPortfolioSummaryResponse = {
  organization_id: string;
  total_open: number;
  total_open_critical: number;
  critical_open_over_14_days: number;
  average_open_days: number | null;
  closed_within_30_days_percent: number | null;
  last_report_at: string | null;
  projects: QualityPortfolioProjectSummary[];
};

/** GET /portfolio/quality-trade-heatmap - roadmap 6.1 */
export type QualityTradeHeatmapCell = {
  trade: string;
  open_total: number;
  open_critical: number;
  open_high: number;
  open_medium: number;
  open_low: number;
};

export type QualityTradeHeatmapResponse = {
  organization_id: string;
  project_id: string | null;
  total_open: number;
  cells: QualityTradeHeatmapCell[];
};

/** GET /portfolio/quality-recurring-rankings - roadmap 6.2 */
export type QualityRecurringIssueRankEntry = {
  issue_id: string;
  title: string;
  trade: string | null;
  location: string | null;
  recurrence_count: number;
  project_id: string;
  project_name: string | null;
  contractor_name: string | null;
  status: QualityIssueStatus;
  severity: QualityIssueSeverity;
};

export type QualityContractorRecurringRankEntry = {
  contractor_name: string;
  recurring_issue_count: number;
  total_recurrence_count: number;
  project_count: number;
};

export type QualityRecurringRankingsResponse = {
  organization_id: string;
  project_id: string | null;
  total_recurring: number;
  issues: QualityRecurringIssueRankEntry[];
  contractors: QualityContractorRecurringRankEntry[];
};

/** GET /portfolio/quality-periodic-report - roadmap 6.3 */
export type QualityPeriodicReportSummary = {
  total_issues: number;
  open_total: number;
  open_critical: number;
  closed_total: number;
  recurring_total: number;
};

export type QualityPeriodicReportProjectRow = {
  project_id: string;
  project_name: string | null;
  contractor_name: string | null;
  issue_total: number;
  open_total: number;
  open_critical: number;
  recurring_total: number;
};

export type QualityPeriodicReportIssueRow = {
  issue_id: string;
  title: string;
  project_id: string;
  project_name: string | null;
  contractor_name: string | null;
  status: QualityIssueStatus;
  severity: QualityIssueSeverity;
  trade: string | null;
  location: string | null;
  standard_ref: string | null;
  catalog_issue_id: string | null;
  recurrence_count: number;
  first_seen_at: string | null;
  last_seen_at: string | null;
};

export type QualityPeriodicReportResponse = {
  organization_id: string;
  project_id: string | null;
  period_days: number;
  period_start: string;
  period_end: string;
  generated_at: string;
  summary: QualityPeriodicReportSummary;
  projects: QualityPeriodicReportProjectRow[];
  issues: QualityPeriodicReportIssueRow[];
};

/** Linked catalog section on issue detail - roadmap 6.5 */
export type QualityIssueCatalogLink = {
  issue_id: string;
  issue_name_he: string;
  top_family: string;
  category_id: string;
  category_name_he: string;
  standard_ref: string | null;
  category_standard_id: string | null;
};

function isIssueVisibility(value: unknown): value is IssueVisibility {
  return (
    typeof value === "string" &&
    (ISSUE_VISIBILITIES as readonly string[]).includes(value)
  );
}

function isQualityIssueSeverity(value: unknown): value is QualityIssueSeverity {
  return (
    typeof value === "string" &&
    (QUALITY_ISSUE_SEVERITIES as readonly string[]).includes(value)
  );
}

function isQualityIssueStatus(value: unknown): value is QualityIssueStatus {
  return (
    typeof value === "string" &&
    (QUALITY_ISSUE_STATUSES as readonly string[]).includes(value)
  );
}

function isQualityIssueEventType(
  value: unknown
): value is QualityIssueEventType {
  return (
    typeof value === "string" &&
    (QUALITY_ISSUE_EVENT_TYPES as readonly string[]).includes(value)
  );
}

function isQualityIssueVisitDiffCategory(
  value: unknown
): value is QualityIssueVisitDiffCategory {
  return (
    typeof value === "string" &&
    (QUALITY_ISSUE_VISIT_DIFF_CATEGORIES as readonly string[]).includes(value)
  );
}

function normalizeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string");
}

/** Normalize API/DB row into a QualityIssue (mirrors parse_quality_issue_row). */
export function parseQualityIssue(row: unknown): QualityIssue {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid quality issue row");
  }

  const record = row as Record<string, unknown>;
  const severity = record.severity;
  const status = record.status;
  const visibilityRaw = record.visibility;

  if (!isQualityIssueSeverity(severity)) {
    throw new Error(`Invalid quality issue severity: ${String(severity)}`);
  }
  if (!isQualityIssueStatus(status)) {
    throw new Error(`Invalid quality issue status: ${String(status)}`);
  }

  const visibility = isIssueVisibility(visibilityRaw)
    ? visibilityRaw
    : "PUBLISHED";

  const recurrenceCount = record.recurrence_count;
  const parsedRecurrence =
    typeof recurrenceCount === "number" && Number.isFinite(recurrenceCount)
      ? Math.max(0, Math.trunc(recurrenceCount))
      : 0;

  return {
    id: String(record.id ?? ""),
    organization_id: String(record.organization_id ?? ""),
    project_id: String(record.project_id ?? ""),
    title: String(record.title ?? ""),
    description:
      record.description == null ? null : String(record.description),
    location: record.location == null ? null : String(record.location),
    trade: record.trade == null ? null : String(record.trade),
    group_key: record.group_key == null ? null : String(record.group_key),
    group_label_he:
      record.group_label_he == null ? null : String(record.group_label_he),
    standard_ref:
      record.standard_ref == null ? null : String(record.standard_ref),
    severity,
    status,
    visibility,
    catalog_issue_id:
      record.catalog_issue_id == null
        ? null
        : String(record.catalog_issue_id),
    first_seen_report_id: String(record.first_seen_report_id ?? ""),
    first_seen_line_id:
      record.first_seen_line_id == null
        ? null
        : String(record.first_seen_line_id),
    first_seen_at: String(record.first_seen_at ?? ""),
    last_seen_report_id: String(record.last_seen_report_id ?? ""),
    last_seen_line_id:
      record.last_seen_line_id == null
        ? null
        : String(record.last_seen_line_id),
    last_seen_at: String(record.last_seen_at ?? ""),
    closed_at: record.closed_at == null ? null : String(record.closed_at),
    closed_by: record.closed_by == null ? null : String(record.closed_by),
    recurrence_count: parsedRecurrence,
    photo_ids: normalizeStringArray(record.photo_ids),
    materialization_key: String(record.materialization_key ?? ""),
    created_at: record.created_at == null ? null : String(record.created_at),
    updated_at: record.updated_at == null ? null : String(record.updated_at),
  };
}

/** Normalize API/DB row into a QualityIssueEvent. */
export function parseQualityIssueEvent(row: unknown): QualityIssueEvent {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid quality issue event row");
  }

  const record = row as Record<string, unknown>;
  const eventType = record.event_type;
  if (!isQualityIssueEventType(eventType)) {
    throw new Error(`Invalid quality issue event type: ${String(eventType)}`);
  }

  const payload =
    record.payload && typeof record.payload === "object"
      ? (record.payload as QualityIssueEvent["payload"])
      : ({} as QualityIssueEvent["payload"]);

  return {
    id: String(record.id ?? ""),
    issue_id: String(record.issue_id ?? ""),
    event_type: eventType,
    report_id: record.report_id == null ? null : String(record.report_id),
    line_id: record.line_id == null ? null : String(record.line_id),
    actor_id: record.actor_id == null ? null : String(record.actor_id),
    payload,
    created_at: record.created_at == null ? null : String(record.created_at),
  };
}

export function parseQualityIssueOpenListResponse(
  body: unknown
): QualityIssueOpenListResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality issue open list response");
  }

  const record = body as Record<string, unknown>;
  const items = Array.isArray(record.items)
    ? record.items.map(parseQualityIssue)
    : [];

  return {
    project_id: String(record.project_id ?? ""),
    total: typeof record.total === "number" ? record.total : items.length,
    items,
  };
}

function parseQualityIssueMatchCandidate(
  row: unknown
): QualityIssueMatchCandidate {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid quality issue match candidate");
  }

  const record = row as Record<string, unknown>;
  const score =
    typeof record.score === "number" && Number.isFinite(record.score)
      ? record.score
      : 0;

  return {
    issue: parseQualityIssue(record.issue),
    match_key: String(record.match_key ?? ""),
    score,
  };
}

export function parseQualityIssueSuggestMatchesResponse(
  body: unknown
): QualityIssueSuggestMatchesResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality issue suggest-matches response");
  }

  const record = body as Record<string, unknown>;
  const candidates = Array.isArray(record.candidates)
    ? record.candidates.map(parseQualityIssueMatchCandidate)
    : [];

  return {
    project_id: String(record.project_id ?? ""),
    match_key: String(record.match_key ?? ""),
    total: typeof record.total === "number" ? record.total : candidates.length,
    candidates,
  };
}

export function parseQualityIssueListResponse(
  body: unknown
): QualityIssueListResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality issue list response");
  }

  const record = body as Record<string, unknown>;
  const items = Array.isArray(record.items)
    ? record.items.map(parseQualityIssue)
    : [];

  return {
    project_id: String(record.project_id ?? ""),
    total: typeof record.total === "number" ? record.total : items.length,
    limit:
      typeof record.limit === "number"
        ? record.limit
        : DEFAULT_QUALITY_ISSUE_LIST_LIMIT,
    offset: typeof record.offset === "number" ? record.offset : 0,
    items,
  };
}

export function parseQualityIssueOrgListResponse(
  body: unknown
): QualityIssueOrgListResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality issue org list response");
  }

  const record = body as Record<string, unknown>;
  const items = Array.isArray(record.items)
    ? record.items.map(parseQualityIssue)
    : [];

  return {
    organization_id: String(record.organization_id ?? ""),
    total: typeof record.total === "number" ? record.total : items.length,
    limit:
      typeof record.limit === "number"
        ? record.limit
        : DEFAULT_QUALITY_ISSUE_LIST_LIMIT,
    offset: typeof record.offset === "number" ? record.offset : 0,
    items,
  };
}

export function parseQualityIssueDetailResponse(
  body: unknown
): QualityIssueDetailResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality issue detail response");
  }

  const record = body as Record<string, unknown>;
  const events = Array.isArray(record.events)
    ? record.events.map(parseQualityIssueEvent)
    : [];

  return {
    issue: parseQualityIssue(record.issue),
    events,
    catalog_link: parseQualityIssueCatalogLink(record.catalog_link),
  };
}

function parseQualityIssueCatalogLink(
  value: unknown
): QualityIssueCatalogLink | null {
  if (value == null) {
    return null;
  }
  if (!value || typeof value !== "object") {
    throw new Error("Invalid quality issue catalog link");
  }

  const record = value as Record<string, unknown>;
  return {
    issue_id: String(record.issue_id ?? ""),
    issue_name_he: String(record.issue_name_he ?? ""),
    top_family: String(record.top_family ?? ""),
    category_id: String(record.category_id ?? ""),
    category_name_he: String(record.category_name_he ?? ""),
    standard_ref:
      record.standard_ref == null ? null : String(record.standard_ref),
    category_standard_id:
      record.category_standard_id == null
        ? null
        : String(record.category_standard_id),
  };
}

function parseQualityIssueVisitDiffEntry(
  row: unknown
): QualityIssueVisitDiffEntry {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid quality issue visit diff entry");
  }

  const record = row as Record<string, unknown>;
  const category = record.category;

  if (!isQualityIssueVisitDiffCategory(category)) {
    throw new Error(`Invalid visit diff category: ${String(category)}`);
  }

  return {
    issue: parseQualityIssue(record.issue),
    line_id: record.line_id == null ? null : String(record.line_id),
    category,
  };
}

export function parseQualityIssueVisitDiffResponse(
  body: unknown
): QualityIssueVisitDiffResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality issue visit diff response");
  }

  const record = body as Record<string, unknown>;
  const parseBucket = (value: unknown): QualityIssueVisitDiffEntry[] =>
    Array.isArray(value) ? value.map(parseQualityIssueVisitDiffEntry) : [];

  const newItems = parseBucket(record.new);
  const closedItems = parseBucket(record.closed);
  const stillOpenItems = parseBucket(record.still_open);
  const recurringItems = parseBucket(record.recurring);

  return {
    project_id: String(record.project_id ?? ""),
    report_id: String(record.report_id ?? ""),
    new: newItems,
    closed: closedItems,
    still_open: stillOpenItems,
    recurring: recurringItems,
    total_new:
      typeof record.total_new === "number" ? record.total_new : newItems.length,
    total_closed:
      typeof record.total_closed === "number"
        ? record.total_closed
        : closedItems.length,
    total_still_open:
      typeof record.total_still_open === "number"
        ? record.total_still_open
        : stillOpenItems.length,
    total_recurring:
      typeof record.total_recurring === "number"
        ? record.total_recurring
        : recurringItems.length,
  };
}

export function parseQualityPortfolioSummaryResponse(
  body: unknown
): QualityPortfolioSummaryResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality portfolio summary response");
  }

  const record = body as Record<string, unknown>;
  const projects = Array.isArray(record.projects)
    ? record.projects.map((project) => {
        const row = project as Record<string, unknown>;
        return {
          project_id: String(row.project_id ?? ""),
          project_name:
            row.project_name == null ? null : String(row.project_name),
          open_total:
            typeof row.open_total === "number" ? row.open_total : 0,
          open_critical:
            typeof row.open_critical === "number" ? row.open_critical : 0,
          critical_open_over_14_days:
            typeof row.critical_open_over_14_days === "number"
              ? row.critical_open_over_14_days
              : 0,
          average_open_days:
            typeof row.average_open_days === "number"
              ? row.average_open_days
              : null,
        } satisfies QualityPortfolioProjectSummary;
      })
    : [];

  return {
    organization_id: String(record.organization_id ?? ""),
    total_open: typeof record.total_open === "number" ? record.total_open : 0,
    total_open_critical:
      typeof record.total_open_critical === "number"
        ? record.total_open_critical
        : 0,
    critical_open_over_14_days:
      typeof record.critical_open_over_14_days === "number"
        ? record.critical_open_over_14_days
        : 0,
    average_open_days:
      typeof record.average_open_days === "number"
        ? record.average_open_days
        : null,
    closed_within_30_days_percent:
      typeof record.closed_within_30_days_percent === "number"
        ? record.closed_within_30_days_percent
        : null,
    last_report_at:
      typeof record.last_report_at === "string"
        ? record.last_report_at
        : null,
    projects,
  };
}

function parseTradeHeatmapCell(row: unknown): QualityTradeHeatmapCell {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid trade heatmap cell");
  }

  const record = row as Record<string, unknown>;
  return {
    trade: String(record.trade ?? ""),
    open_total:
      typeof record.open_total === "number" ? record.open_total : 0,
    open_critical:
      typeof record.open_critical === "number" ? record.open_critical : 0,
    open_high: typeof record.open_high === "number" ? record.open_high : 0,
    open_medium:
      typeof record.open_medium === "number" ? record.open_medium : 0,
    open_low: typeof record.open_low === "number" ? record.open_low : 0,
  };
}

export function parseQualityTradeHeatmapResponse(
  body: unknown
): QualityTradeHeatmapResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality trade heatmap response");
  }

  const record = body as Record<string, unknown>;
  const cells = Array.isArray(record.cells)
    ? record.cells.map(parseTradeHeatmapCell)
    : [];

  return {
    organization_id: String(record.organization_id ?? ""),
    project_id:
      record.project_id == null ? null : String(record.project_id),
    total_open:
      typeof record.total_open === "number" ? record.total_open : 0,
    cells,
  };
}

function parseRecurringIssueRankEntry(
  row: unknown
): QualityRecurringIssueRankEntry {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid recurring issue rank entry");
  }

  const record = row as Record<string, unknown>;
  const status = record.status;
  const severity = record.severity;

  if (!isQualityIssueStatus(status)) {
    throw new Error("Invalid recurring issue status");
  }
  if (!isQualityIssueSeverity(severity)) {
    throw new Error("Invalid recurring issue severity");
  }

  const recurrenceCount = record.recurrence_count;
  if (typeof recurrenceCount !== "number" || recurrenceCount < 1) {
    throw new Error("Invalid recurrence_count");
  }

  return {
    issue_id: String(record.issue_id ?? ""),
    title: String(record.title ?? ""),
    trade: record.trade == null ? null : String(record.trade),
    location: record.location == null ? null : String(record.location),
    recurrence_count: recurrenceCount,
    project_id: String(record.project_id ?? ""),
    project_name:
      record.project_name == null ? null : String(record.project_name),
    contractor_name:
      record.contractor_name == null ? null : String(record.contractor_name),
    status,
    severity,
  };
}

function parseContractorRecurringRankEntry(
  row: unknown
): QualityContractorRecurringRankEntry {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid contractor recurring rank entry");
  }

  const record = row as Record<string, unknown>;
  return {
    contractor_name: String(record.contractor_name ?? ""),
    recurring_issue_count:
      typeof record.recurring_issue_count === "number"
        ? record.recurring_issue_count
        : 0,
    total_recurrence_count:
      typeof record.total_recurrence_count === "number"
        ? record.total_recurrence_count
        : 0,
    project_count:
      typeof record.project_count === "number" ? record.project_count : 0,
  };
}

export function parseQualityRecurringRankingsResponse(
  body: unknown
): QualityRecurringRankingsResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality recurring rankings response");
  }

  const record = body as Record<string, unknown>;
  const issues = Array.isArray(record.issues)
    ? record.issues.map(parseRecurringIssueRankEntry)
    : [];
  const contractors = Array.isArray(record.contractors)
    ? record.contractors.map(parseContractorRecurringRankEntry)
    : [];

  return {
    organization_id: String(record.organization_id ?? ""),
    project_id:
      record.project_id == null ? null : String(record.project_id),
    total_recurring:
      typeof record.total_recurring === "number" ? record.total_recurring : 0,
    issues,
    contractors,
  };
}

function parsePeriodicReportSummary(row: unknown): QualityPeriodicReportSummary {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid periodic report summary");
  }

  const record = row as Record<string, unknown>;
  return {
    total_issues:
      typeof record.total_issues === "number" ? record.total_issues : 0,
    open_total: typeof record.open_total === "number" ? record.open_total : 0,
    open_critical:
      typeof record.open_critical === "number" ? record.open_critical : 0,
    closed_total:
      typeof record.closed_total === "number" ? record.closed_total : 0,
    recurring_total:
      typeof record.recurring_total === "number" ? record.recurring_total : 0,
  };
}

function parsePeriodicReportProjectRow(
  row: unknown
): QualityPeriodicReportProjectRow {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid periodic report project row");
  }

  const record = row as Record<string, unknown>;
  return {
    project_id: String(record.project_id ?? ""),
    project_name:
      record.project_name == null ? null : String(record.project_name),
    contractor_name:
      record.contractor_name == null ? null : String(record.contractor_name),
    issue_total:
      typeof record.issue_total === "number" ? record.issue_total : 0,
    open_total: typeof record.open_total === "number" ? record.open_total : 0,
    open_critical:
      typeof record.open_critical === "number" ? record.open_critical : 0,
    recurring_total:
      typeof record.recurring_total === "number" ? record.recurring_total : 0,
  };
}

function parsePeriodicReportIssueRow(
  row: unknown
): QualityPeriodicReportIssueRow {
  if (!row || typeof row !== "object") {
    throw new Error("Invalid periodic report issue row");
  }

  const record = row as Record<string, unknown>;
  const status = record.status;
  const severity = record.severity;

  if (!isQualityIssueStatus(status)) {
    throw new Error("Invalid periodic report issue status");
  }
  if (!isQualityIssueSeverity(severity)) {
    throw new Error("Invalid periodic report issue severity");
  }

  return {
    issue_id: String(record.issue_id ?? ""),
    title: String(record.title ?? ""),
    project_id: String(record.project_id ?? ""),
    project_name:
      record.project_name == null ? null : String(record.project_name),
    contractor_name:
      record.contractor_name == null ? null : String(record.contractor_name),
    status,
    severity,
    trade: record.trade == null ? null : String(record.trade),
    location: record.location == null ? null : String(record.location),
    standard_ref:
      record.standard_ref == null ? null : String(record.standard_ref),
    catalog_issue_id:
      record.catalog_issue_id == null ? null : String(record.catalog_issue_id),
    recurrence_count:
      typeof record.recurrence_count === "number" ? record.recurrence_count : 0,
    first_seen_at:
      record.first_seen_at == null ? null : String(record.first_seen_at),
    last_seen_at:
      record.last_seen_at == null ? null : String(record.last_seen_at),
  };
}

export function parseQualityPeriodicReportResponse(
  body: unknown
): QualityPeriodicReportResponse {
  if (!body || typeof body !== "object") {
    throw new Error("Invalid quality periodic report response");
  }

  const record = body as Record<string, unknown>;
  const projects = Array.isArray(record.projects)
    ? record.projects.map(parsePeriodicReportProjectRow)
    : [];
  const issues = Array.isArray(record.issues)
    ? record.issues.map(parsePeriodicReportIssueRow)
    : [];

  return {
    organization_id: String(record.organization_id ?? ""),
    project_id:
      record.project_id == null ? null : String(record.project_id),
    period_days:
      typeof record.period_days === "number" ? record.period_days : 30,
    period_start: String(record.period_start ?? ""),
    period_end: String(record.period_end ?? ""),
    generated_at: String(record.generated_at ?? ""),
    summary: parsePeriodicReportSummary(record.summary),
    projects,
    issues,
  };
}

/** Apply create-request defaults for last_seen fields (mirrors backend validator). */
export function withCreateRequestDefaults(
  request: QualityIssueCreateRequest
): QualityIssueCreateRequest {
  return {
    ...request,
    last_seen_report_id:
      request.last_seen_report_id ?? request.first_seen_report_id,
    last_seen_line_id:
      request.last_seen_line_id ?? request.first_seen_line_id ?? null,
    last_seen_at: request.last_seen_at ?? request.first_seen_at,
    severity: request.severity ?? DEFAULT_QUALITY_ISSUE_SEVERITY,
    visibility: request.visibility ?? DEFAULT_ISSUE_VISIBILITY,
    photo_ids: request.photo_ids ?? [],
  };
}

export function buildQualityIssueListQueryParams(
  query: QualityIssueListQuery = {}
): URLSearchParams {
  const params = new URLSearchParams();
  const limit = query.limit ?? DEFAULT_QUALITY_ISSUE_LIST_LIMIT;
  const offset = query.offset ?? 0;

  params.set("limit", String(limit));
  params.set("offset", String(offset));

  for (const status of query.status ?? []) {
    params.append("status", status);
  }
  for (const severity of query.severity ?? []) {
    params.append("severity", severity);
  }
  if (query.trade?.trim()) {
    params.set("trade", query.trade.trim());
  }
  if (query.search?.trim()) {
    params.set("search", query.search.trim());
  }

  return params;
}
