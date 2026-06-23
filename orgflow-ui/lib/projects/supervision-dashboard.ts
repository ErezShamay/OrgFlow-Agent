import { apiFetch } from "@/lib/api/client";
import { readApiErrorMessage } from "@/lib/api/read-error-message";
import { hasQCPermission } from "@/lib/quality-issues/permissions";
import {
  parseProjectSupervisionDashboard,
  parseSupervisionProjectSummaries,
  parseSupervisionTradeDetail,
  type ProjectSupervisionDashboard,
  type SupervisionProjectSummaries,
  type SupervisionTradeDetail,
} from "@/lib/projects/supervision-dashboard-types";

export {
  parseProjectSupervisionDashboard,
  SUPERVISION_OVERALL_STATUS_BADGE,
  SUPERVISION_OVERALL_STATUS_LABELS,
  SUPERVISION_TRADE_BAR_COLORS,
  supervisionTradeBarColor,
} from "@/lib/projects/supervision-dashboard-types";
export type {
  ProjectSupervisionDashboard,
  SupervisionApartmentProgress,
  SupervisionDashboardKpis,
  SupervisionOverallStatus,
  SupervisionProjectSummaries,
  SupervisionProjectSummary,
  SupervisionPublicAreaProgress,
  SupervisionTradeDetail,
  SupervisionTradeLineItem,
  SupervisionTradeProgress,
} from "@/lib/projects/supervision-dashboard-types";

export class SupervisionDashboardApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "SupervisionDashboardApiError";
    this.status = status;
  }
}

export function buildProjectSupervisionDashboardPath(projectId: string): string {
  return `/projects/${encodeURIComponent(projectId)}/supervision-dashboard`;
}

export function buildProjectSupervisionSummariesPath(): string {
  return "/projects/supervision-summaries";
}

export function buildProjectSupervisionTradeDetailPath(
  projectId: string,
  tradeKey: string
): string {
  return `/projects/${encodeURIComponent(projectId)}/supervision-dashboard/trades/${encodeURIComponent(tradeKey)}`;
}

export function projectSupervisionTradePagePath(
  projectId: string,
  tradeKey: string
): string {
  return `/projects/${encodeURIComponent(projectId)}/trades/${encodeURIComponent(tradeKey)}`;
}

/** Supervisors and admins with field-report access see the project dashboard. */
export function canViewProjectSupervisionDashboard(role?: string | null): boolean {
  return (
    hasQCPermission(role, "projects:read")
    && hasQCPermission(role, "field_reports:read")
  );
}

export async function fetchProjectSupervisionDashboard(
  projectId: string
): Promise<ProjectSupervisionDashboard> {
  const response = await apiFetch(buildProjectSupervisionDashboardPath(projectId));

  if (!response.ok) {
    const message = await readApiErrorMessage(
      response,
      "שגיאה בטעינת דשבורד הפרויקט"
    );
    throw new SupervisionDashboardApiError(message, response.status);
  }

  const payload = await response.json();
  return parseProjectSupervisionDashboard(payload);
}

export async function fetchProjectSupervisionSummaries(): Promise<SupervisionProjectSummaries> {
  const response = await apiFetch(buildProjectSupervisionSummariesPath());

  if (!response.ok) {
    const message = await readApiErrorMessage(
      response,
      "שגיאה בטעינת סיכומי פיקוח"
    );
    throw new SupervisionDashboardApiError(message, response.status);
  }

  const payload = await response.json();
  return parseSupervisionProjectSummaries(payload);
}

export async function fetchProjectSupervisionTradeDetail(
  projectId: string,
  tradeKey: string
): Promise<SupervisionTradeDetail> {
  const response = await apiFetch(
    buildProjectSupervisionTradeDetailPath(projectId, tradeKey)
  );

  if (!response.ok) {
    const message = await readApiErrorMessage(
      response,
      "שגיאה בטעינת פירוט המלאכה"
    );
    throw new SupervisionDashboardApiError(message, response.status);
  }

  const payload = await response.json();
  return parseSupervisionTradeDetail(payload);
}

export function projectSupervisionVisitReportPath(
  projectId: string,
  apartmentNumber: string,
  apartmentId?: string | null
): string {
  const params = new URLSearchParams({
    apartment_number: apartmentNumber,
  });
  if (apartmentId) {
    params.set("apartment_id", apartmentId);
  }
  return `/projects/${encodeURIComponent(projectId)}/field-reports/new?${params.toString()}`;
}

export function projectSupervisionPublicAreaVisitReportPath(
  projectId: string,
  publicAreaId: string
): string {
  const params = new URLSearchParams({
    public_area_id: publicAreaId,
  });
  return `/projects/${encodeURIComponent(projectId)}/field-reports/new?${params.toString()}`;
}

export function projectApartmentPortalPath(
  projectId: string,
  apartmentId: string
): string {
  return `/projects/${encodeURIComponent(projectId)}/apartments/${encodeURIComponent(apartmentId)}`;
}
