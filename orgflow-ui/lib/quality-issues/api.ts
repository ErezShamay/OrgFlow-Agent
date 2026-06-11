/**
 * QC Issue Registry API client (roadmap 1.3.2).
 * Mirrors backend routes in app/main.py.
 */

import { apiFetch } from "@/lib/api/client";
import { readApiErrorMessage } from "@/lib/api/read-error-message";
import type {
  QualityIssue,
  QualityIssueCreateRequest,
  QualityIssueDetailResponse,
  QualityIssueListQuery,
  QualityIssueListResponse,
  QualityIssueOrgListResponse,
  QualityIssueOpenListResponse,
  QualityIssueSuggestMatchesRequest,
  QualityIssueSuggestMatchesResponse,
  QualityIssueUpdateRequest,
  QualityIssueVisitDiffResponse,
  QualityPeriodicReportResponse,
  QualityPortfolioSummaryResponse,
  QualityRecurringRankingsResponse,
  QualityTradeHeatmapResponse,
} from "@/lib/quality-issues/types";
import {
  buildQualityIssueListQueryParams,
  parseQualityIssue,
  parseQualityIssueDetailResponse,
  parseQualityIssueListResponse,
  parseQualityIssueOrgListResponse,
  parseQualityIssueOpenListResponse,
  parseQualityIssueSuggestMatchesResponse,
  parseQualityIssueVisitDiffResponse,
  parseQualityPeriodicReportResponse,
  parseQualityPortfolioSummaryResponse,
  parseQualityRecurringRankingsResponse,
  parseQualityTradeHeatmapResponse,
  withCreateRequestDefaults,
} from "@/lib/quality-issues/types";

export class QualityIssueApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "QualityIssueApiError";
    this.status = status;
  }
}

const QUALITY_ISSUE_ERROR_MESSAGES: Record<string, string> = {
  ISSUE_NOT_FOUND: "הליקוי לא נמצא",
  PROJECT_NOT_FOUND: "הפרויקט לא נמצא",
  INVALID_STATUS_TRANSITION: "מעבר סטטוס לא חוקי",
  FORBIDDEN: "אין הרשאה לבצע פעולה זו",
};

export function buildProjectIssuesPath(projectId: string): string {
  return `/projects/${encodeURIComponent(projectId)}/issues`;
}

export function buildProjectOpenIssuesPath(projectId: string): string {
  return `${buildProjectIssuesPath(projectId)}/open`;
}

export function buildProjectSuggestMatchesPath(projectId: string): string {
  return `${buildProjectIssuesPath(projectId)}/suggest-matches`;
}

export function buildIssuePath(issueId: string): string {
  return `/issues/${encodeURIComponent(issueId)}`;
}

export function buildIssuePhotosPath(issueId: string): string {
  return `${buildIssuePath(issueId)}/photos`;
}

export function buildIssuePhotoPath(issueId: string, photoId: string): string {
  return `${buildIssuePhotosPath(issueId)}/${encodeURIComponent(photoId)}`;
}

export function buildOrganizationIssuesPath(): string {
  return "/issues";
}

export function buildPortfolioQualitySummaryPath(): string {
  return "/portfolio/quality-summary";
}

export function buildPortfolioTradeHeatmapPath(
  projectId?: string | null
): string {
  const path = "/portfolio/quality-trade-heatmap";
  const normalized = projectId?.trim();
  if (!normalized) {
    return path;
  }

  const params = new URLSearchParams({ project_id: normalized });
  return `${path}?${params.toString()}`;
}

export function buildPortfolioRecurringRankingsPath(
  projectId?: string | null
): string {
  const path = "/portfolio/quality-recurring-rankings";
  const normalized = projectId?.trim();
  if (!normalized) {
    return path;
  }

  const params = new URLSearchParams({ project_id: normalized });
  return `${path}?${params.toString()}`;
}

export function buildPortfolioPeriodicReportPath(
  periodDays: number = 30,
  projectId?: string | null
): string {
  const params = new URLSearchParams({
    period_days: String(Math.max(1, periodDays)),
  });
  const normalized = projectId?.trim();
  if (normalized) {
    params.set("project_id", normalized);
  }
  return `/portfolio/quality-periodic-report?${params.toString()}`;
}

export function buildPortfolioPeriodicReportExportPath(
  periodDays: number = 30,
  projectId?: string | null
): string {
  const params = new URLSearchParams({
    period_days: String(Math.max(1, periodDays)),
    format: "csv",
  });
  const normalized = projectId?.trim();
  if (normalized) {
    params.set("project_id", normalized);
  }
  return `/portfolio/quality-periodic-report/export?${params.toString()}`;
}

export function buildProjectVisitIssueDiffPath(
  projectId: string,
  reportId: string
): string {
  return `/projects/${encodeURIComponent(projectId)}/visits/${encodeURIComponent(reportId)}/issue-diff`;
}

async function parseQualityIssueApiError(
  response: Response,
  fallback: string
): Promise<never> {
  const message = await readApiErrorMessage(
    response,
    fallback,
    QUALITY_ISSUE_ERROR_MESSAGES
  );
  throw new QualityIssueApiError(message, response.status);
}

export async function listProjectOpenQualityIssues(
  projectId: string
): Promise<QualityIssueOpenListResponse> {
  const response = await apiFetch(buildProjectOpenIssuesPath(projectId));

  if (!response.ok) {
    return parseQualityIssueApiError(
      response,
      "שגיאה בטעינת ליקויים פתוחים"
    );
  }

  return parseQualityIssueOpenListResponse(await response.json());
}

export async function suggestProjectQualityIssueMatches(
  projectId: string,
  request: QualityIssueSuggestMatchesRequest
): Promise<QualityIssueSuggestMatchesResponse> {
  const response = await apiFetch(buildProjectSuggestMatchesPath(projectId), {
    method: "POST",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    return parseQualityIssueApiError(
      response,
      "שגיאה בחיפוש ליקויים דומים"
    );
  }

  return parseQualityIssueSuggestMatchesResponse(await response.json());
}

export async function listOrganizationQualityIssues(
  query: QualityIssueListQuery = {}
): Promise<QualityIssueOrgListResponse> {
  const params = buildQualityIssueListQueryParams(query);
  const path = `${buildOrganizationIssuesPath()}?${params.toString()}`;
  const response = await apiFetch(path);

  if (!response.ok) {
    return parseQualityIssueApiError(
      response,
      "שגיאה בטעינת רשימת הליקויים"
    );
  }

  return parseQualityIssueOrgListResponse(await response.json());
}

export async function listProjectQualityIssues(
  projectId: string,
  query: QualityIssueListQuery = {}
): Promise<QualityIssueListResponse> {
  const params = buildQualityIssueListQueryParams(query);
  const path = `${buildProjectIssuesPath(projectId)}?${params.toString()}`;
  const response = await apiFetch(path);

  if (!response.ok) {
    return parseQualityIssueApiError(
      response,
      "שגיאה בטעינת רשימת הליקויים"
    );
  }

  return parseQualityIssueListResponse(await response.json());
}

export async function createProjectQualityIssue(
  projectId: string,
  request: QualityIssueCreateRequest
): Promise<QualityIssue> {
  const body = withCreateRequestDefaults(request);
  const response = await apiFetch(buildProjectIssuesPath(projectId), {
    method: "POST",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    return parseQualityIssueApiError(response, "שגיאה ביצירת ליקוי");
  }

  return parseQualityIssue(await response.json());
}

export async function getQualityIssueDetail(
  issueId: string
): Promise<QualityIssueDetailResponse> {
  const response = await apiFetch(buildIssuePath(issueId));

  if (!response.ok) {
    return parseQualityIssueApiError(response, "שגיאה בטעינת פרטי הליקוי");
  }

  return parseQualityIssueDetailResponse(await response.json());
}

export async function updateQualityIssue(
  issueId: string,
  request: QualityIssueUpdateRequest
): Promise<QualityIssue> {
  const response = await apiFetch(buildIssuePath(issueId), {
    method: "PATCH",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    return parseQualityIssueApiError(response, "שגיאה בעדכון הליקוי");
  }

  return parseQualityIssue(await response.json());
}

export async function getProjectVisitIssueDiff(
  projectId: string,
  reportId: string
): Promise<QualityIssueVisitDiffResponse> {
  const response = await apiFetch(
    buildProjectVisitIssueDiffPath(projectId, reportId)
  );

  if (!response.ok) {
    return parseQualityIssueApiError(
      response,
      "שגיאה בטעינת שינויי ליקויים בביקור"
    );
  }

  return parseQualityIssueVisitDiffResponse(await response.json());
}

export async function getPortfolioQualitySummary(): Promise<QualityPortfolioSummaryResponse> {
  const response = await apiFetch(buildPortfolioQualitySummaryPath());

  if (!response.ok) {
    return parseQualityIssueApiError(
      response,
      "שגיאה בטעינת סיכום תיק בקרת איכות"
    );
  }

  return parseQualityPortfolioSummaryResponse(await response.json());
}

export async function getPortfolioTradeHeatmap(
  projectId?: string | null
): Promise<QualityTradeHeatmapResponse> {
  const response = await apiFetch(buildPortfolioTradeHeatmapPath(projectId));

  if (!response.ok) {
    return parseQualityIssueApiError(
      response,
      "שגיאה בטעינת מפת חום לפי מלאכה"
    );
  }

  return parseQualityTradeHeatmapResponse(await response.json());
}

export async function getPortfolioRecurringRankings(
  projectId?: string | null
): Promise<QualityRecurringRankingsResponse> {
  const response = await apiFetch(
    buildPortfolioRecurringRankingsPath(projectId)
  );

  if (!response.ok) {
    return parseQualityIssueApiError(
      response,
      "שגיאה בטעינת דירוג ליקויים חוזרים"
    );
  }

  return parseQualityRecurringRankingsResponse(await response.json());
}

export async function getPortfolioPeriodicReport(
  periodDays: number = 30,
  projectId?: string | null
): Promise<QualityPeriodicReportResponse> {
  const response = await apiFetch(
    buildPortfolioPeriodicReportPath(periodDays, projectId)
  );

  if (!response.ok) {
    return parseQualityIssueApiError(
      response,
      "שגיאה בטעינת דוח תקופתי"
    );
  }

  return parseQualityPeriodicReportResponse(await response.json());
}
