/** Types for GET /projects/{project_id}/supervision-dashboard (gates D3–D4). */

export type SupervisionOverallStatus = "healthy" | "attention" | "critical";

export type SupervisionDashboardKpis = {
  in_treatment: number;
  with_defects: number;
  completed: number;
  total_items: number;
  progress_percent: number;
};

export type SupervisionTradeProgress = {
  trade_key: string;
  label_he: string;
  total_items: number;
  completed: number;
  with_defects: number;
  in_treatment: number;
  progress_percent: number;
};

export type SupervisionApartmentProgress = {
  apartment_id: string | null;
  apartment_number: string;
  group_key: string;
  total_items: number;
  completed: number;
  with_defects: number;
  in_treatment: number;
  open_issues_count: number;
  progress_percent: number;
  last_visit_report_id: string | null;
  last_visit_at: string | null;
};

export type SupervisionPublicAreaProgress = {
  area_key: string;
  label_he: string;
  total_items: number;
  completed: number;
  with_defects: number;
  in_treatment: number;
  open_issues_count: number;
  progress_percent: number;
  last_visit_report_id: string | null;
  last_visit_at: string | null;
};

export type ProjectSupervisionDashboard = {
  project_id: string;
  project_name: string;
  overall_status: SupervisionOverallStatus;
  kpis: SupervisionDashboardKpis;
  trades: SupervisionTradeProgress[];
  apartments: SupervisionApartmentProgress[];
  public_areas: SupervisionPublicAreaProgress[];
};

export const SUPERVISION_OVERALL_STATUS_LABELS: Record<
  SupervisionOverallStatus,
  string
> = {
  healthy: "תקין",
  attention: "דורש טיפול",
  critical: "קריטי",
};

export const SUPERVISION_OVERALL_STATUS_BADGE: Record<
  SupervisionOverallStatus,
  "success" | "warning" | "danger"
> = {
  healthy: "success",
  attention: "warning",
  critical: "danger",
};

/** Trade progress bar accent colors (ProVisor-style rotation). */
export const SUPERVISION_TRADE_BAR_COLORS = [
  "bg-sky-500",
  "bg-violet-500",
  "bg-emerald-500",
  "bg-amber-500",
  "bg-rose-500",
  "bg-cyan-500",
  "bg-indigo-500",
  "bg-orange-500",
  "bg-teal-500",
  "bg-fuchsia-500",
] as const;

export function supervisionTradeBarColor(index: number): string {
  return SUPERVISION_TRADE_BAR_COLORS[
    index % SUPERVISION_TRADE_BAR_COLORS.length
  ];
}

export function projectSupervisionTradePagePath(
  projectId: string,
  tradeKey: string
): string {
  return `/projects/${encodeURIComponent(projectId)}/trades/${encodeURIComponent(tradeKey)}`;
}

export type SupervisionProjectSummary = {
  project_id: string;
  overall_status: SupervisionOverallStatus;
  progress_percent: number;
};

export type SupervisionProjectSummaries = {
  items: SupervisionProjectSummary[];
};

export type SupervisionTradeLineItem = {
  scope_label_he: string;
  apartment_number: string | null;
  apartment_id: string | null;
  item_name_he: string;
  status: string;
  display_status_he: string;
  linked_issue_id: string | null;
};

export type SupervisionTradeDetail = {
  project_id: string;
  project_name: string;
  trade_key: string;
  label_he: string;
  kpis: SupervisionDashboardKpis;
  items: SupervisionTradeLineItem[];
};

export function parseSupervisionProjectSummaries(
  payload: unknown
): SupervisionProjectSummaries {
  const data = payload as SupervisionProjectSummaries;
  return {
    items: Array.isArray(data.items) ? data.items : [],
  };
}

export function parseSupervisionTradeDetail(
  payload: unknown
): SupervisionTradeDetail {
  const data = payload as SupervisionTradeDetail;
  return {
    project_id: String(data.project_id ?? ""),
    project_name: String(data.project_name ?? ""),
    trade_key: String(data.trade_key ?? ""),
    label_he: String(data.label_he ?? ""),
    kpis: {
      in_treatment: Number(data.kpis?.in_treatment ?? 0),
      with_defects: Number(data.kpis?.with_defects ?? 0),
      completed: Number(data.kpis?.completed ?? 0),
      total_items: Number(data.kpis?.total_items ?? 0),
      progress_percent: Number(data.kpis?.progress_percent ?? 0),
    },
    items: Array.isArray(data.items) ? data.items : [],
  };
}

export function parseProjectSupervisionDashboard(
  payload: unknown
): ProjectSupervisionDashboard {
  const data = payload as ProjectSupervisionDashboard;
  return {
    project_id: String(data.project_id ?? ""),
    project_name: String(data.project_name ?? ""),
    overall_status: data.overall_status ?? "healthy",
    kpis: {
      in_treatment: Number(data.kpis?.in_treatment ?? 0),
      with_defects: Number(data.kpis?.with_defects ?? 0),
      completed: Number(data.kpis?.completed ?? 0),
      total_items: Number(data.kpis?.total_items ?? 0),
      progress_percent: Number(data.kpis?.progress_percent ?? 0),
    },
    trades: Array.isArray(data.trades) ? data.trades : [],
    apartments: Array.isArray(data.apartments) ? data.apartments : [],
    public_areas: Array.isArray(data.public_areas) ? data.public_areas : [],
  };
}
