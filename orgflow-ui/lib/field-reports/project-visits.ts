import { apiFetch } from "@/lib/api/client";
import { readApiErrorMessage } from "@/lib/api/read-error-message";

export type ProjectFieldVisitListItem = {
  id: string;
  project_id: string;
  visit_date: string;
  visit_type_label_he: string;
  status: string;
  status_label_he?: string;
};

type ProjectFieldVisitListResponse = {
  reports: ProjectFieldVisitListItem[];
};

export function buildProjectFieldVisitsPath(projectId: string): string {
  const params = new URLSearchParams({
    project_id: projectId,
  });
  return `/field-reports/visits?${params.toString()}`;
}

function parseProjectFieldVisitListItem(
  value: unknown
): ProjectFieldVisitListItem | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const record = value as Record<string, unknown>;
  const id = typeof record.id === "string" ? record.id.trim() : "";
  const project_id =
    typeof record.project_id === "string" ? record.project_id.trim() : "";
  const visit_date =
    typeof record.visit_date === "string" ? record.visit_date.trim() : "";
  const visit_type_label_he =
    typeof record.visit_type_label_he === "string"
      ? record.visit_type_label_he.trim()
      : "";
  const status = typeof record.status === "string" ? record.status.trim() : "";

  if (!id || !project_id || !visit_date || !visit_type_label_he || !status) {
    return null;
  }

  return {
    id,
    project_id,
    visit_date,
    visit_type_label_he,
    status,
    status_label_he:
      typeof record.status_label_he === "string"
        ? record.status_label_he.trim()
        : undefined,
  };
}

export function parseProjectFieldVisitListResponse(
  payload: unknown
): ProjectFieldVisitListResponse {
  if (!payload || typeof payload !== "object") {
    return { reports: [] };
  }

  const reports = (payload as { reports?: unknown }).reports;
  if (!Array.isArray(reports)) {
    return { reports: [] };
  }

  return {
    reports: reports
      .map(parseProjectFieldVisitListItem)
      .filter((item): item is ProjectFieldVisitListItem => item !== null),
  };
}

export async function listProjectFieldVisitReports(
  projectId: string
): Promise<ProjectFieldVisitListResponse> {
  const response = await apiFetch(buildProjectFieldVisitsPath(projectId));

  if (!response.ok) {
    const message = await readApiErrorMessage(
      response,
      "שגיאה בטעינת דוחות ביקור לפרויקט"
    );
    throw new Error(message);
  }

  return parseProjectFieldVisitListResponse(await response.json());
}
