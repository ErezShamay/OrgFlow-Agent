export type InviteStatus = "none" | "pending" | "active";

export type ProjectApartment = {
  id: string;
  organization_id: string;
  project_id: string;
  apartment_number: string;
  group_key: string;
  owner_name: string;
  phone?: string | null;
  email?: string | null;
  building?: string | null;
  entrance?: string | null;
  resident_profile_id?: string | null;
  invite_status: InviteStatus;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ResidentPortalProgressItem = {
  description: string;
  status: string;
  completion_date: string;
  report_id: string;
  visit_date?: string | null;
  report_title?: string | null;
};

export type ReportSource = "field_visit" | "weekly" | "legacy";

export type ResidentPortalReportLine = {
  id: string;
  report_id: string;
  description?: string | null;
  status?: string | null;
  location?: string | null;
  visit_date?: string | null;
  report_title?: string | null;
  source?: ReportSource;
};

export type ResidentPortalReportSummary = {
  id: string;
  title?: string | null;
  visit_type?: string | null;
  visit_date?: string | null;
  status?: string | null;
  pdf_url?: string | null;
  line_count: number;
  source?: ReportSource;
};

export type ResidentPortalGanttMilestone = {
  date: string;
  label: string;
  kind: "progress" | "inspection" | "completion";
  status?: string | null;
};

export type ResidentPortalGanttRow = {
  task_key: string;
  label: string;
  status?: string;
  start_date?: string | null;
  end_date?: string | null;
  milestones: ResidentPortalGanttMilestone[];
};

export type ResidentPortalIssueSummary = {
  id: string;
  title?: string | null;
  status?: string | null;
  tenant_view_status_he?: string | null;
  trade?: string | null;
  location?: string | null;
  severity?: string | null;
  catalog_issue_id?: string | null;
  standard_ref?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
};

export type ResidentPortalStatusLevel = "green" | "yellow" | "red";

export type ResidentPortalStatusCard = {
  card_key: string;
  title: string;
  level: ResidentPortalStatusLevel;
  open_count: number;
  closed_count: number;
  critical_open_count: number;
  issue_count: number;
};

export type ResidentPortalPdfDownload = {
  report_id: string;
  title?: string | null;
  visit_date?: string | null;
  pdf_url: string;
  source?: ReportSource;
};

export type ResidentPortalPayload = {
  apartment: ProjectApartment;
  project_name?: string | null;
  default_view: "trust_dashboard";
  status_cards: ResidentPortalStatusCard[];
  pdf_downloads: ResidentPortalPdfDownload[];
  reports: ResidentPortalReportSummary[];
  report_lines: ResidentPortalReportLine[];
  issues: ResidentPortalIssueSummary[];
  progress_timeline: ResidentPortalProgressItem[];
  gantt_rows: ResidentPortalGanttRow[];
  read_only: boolean;
};

const STATUS_LEVEL_LABELS: Record<ResidentPortalStatusLevel, string> = {
  green: "תקין",
  yellow: "בטיפול",
  red: "דורש תשומת לב",
};

const STATUS_LEVEL_EMOJI: Record<ResidentPortalStatusLevel, string> = {
  green: "🟢",
  yellow: "🟡",
  red: "🔴",
};

export function residentStatusLevelLabel(level: ResidentPortalStatusLevel): string {
  return STATUS_LEVEL_LABELS[level];
}

export function residentStatusLevelEmoji(level: ResidentPortalStatusLevel): string {
  return STATUS_LEVEL_EMOJI[level];
}

const REPORT_SOURCE_LABELS: Record<ReportSource, string> = {
  field_visit: "דוח שטח",
  weekly: "דוח שבועי",
  legacy: "דוח שהועלה",
};

export function reportSourceLabel(source?: ReportSource): string {
  if (!source) return REPORT_SOURCE_LABELS.field_visit;
  return REPORT_SOURCE_LABELS[source] ?? source;
}
