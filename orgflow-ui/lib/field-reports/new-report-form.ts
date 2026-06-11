import {
  normalizeHeaderFields,
  serializeHeaderFieldsForApi,
} from "@/lib/field-reports/header-fields";
import {
  applyProjectPrefillToHeaderFields,
  projectPrefillSourceFromRecord,
  type ProjectPrefillSource,
} from "@/lib/field-reports/project-header-prefill";
import type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";
import {
  saveLocalReport,
  type LocalVisitReportRecord,
} from "@/lib/field-reports/repositories/reports-repository";
import { apiFetch } from "@/lib/api/client";

export type NewReportProject = {
  id: string;
  project_name: string;
  prefill?: ProjectPrefillSource | null;
};

export type NewReportVisitType = {
  code: string;
  label_he: string;
};

export type NewReportFormData = {
  projects: NewReportProject[];
  visitTypes: NewReportVisitType[];
};

export function parseNewReportFormFromCatalog(
  bundle: OfflinePrepBundle
): NewReportFormData {
  const projects = (bundle.projects as Array<Record<string, unknown>>)
    .map((project) => ({
      id: String(project.id ?? ""),
      project_name: String(
        project.project_name ?? project.id ?? "פרויקט"
      ),
      prefill: projectPrefillSourceFromRecord(project),
    }))
    .filter((project) => project.id);

  const visitTypes = (bundle.visit_types as Array<Record<string, unknown>>)
    .map((visitType) => ({
      code: String(visitType.code ?? ""),
      label_he: String(visitType.label_he ?? visitType.code ?? ""),
    }))
    .filter((visitType) => visitType.code);

  return { projects, visitTypes };
}

export type CreateLocalVisitReportParams = {
  organizationId: string;
  userId?: string | null;
  projectId: string;
  projectName?: string | null;
  visitType: string;
  visitTypeLabelHe?: string | null;
  visitDate: string;
  catalogVersion?: string | null;
  organizationProfileSnapshot?: Record<string, unknown> | null;
  projectPrefill?: ProjectPrefillSource | null;
};

/** יוצר דוח מקומי עם UUID - מקור אמת בשטח (FR-011). */
export async function createLocalVisitReport(
  params: CreateLocalVisitReportParams
): Promise<LocalVisitReportRecord> {
  let normalized = normalizeHeaderFields({}, params.visitType, {
    visitDate: params.visitDate,
  });

  if (params.projectPrefill) {
    normalized = applyProjectPrefillToHeaderFields(
      normalized,
      params.projectPrefill
    );
  }

  const headerFields = serializeHeaderFieldsForApi(normalized);

  return saveLocalReport({
    organization_id: params.organizationId,
    user_id: params.userId ?? null,
    project_id: params.projectId,
    project_name: params.projectName ?? null,
    visit_type: params.visitType,
    visit_type_label_he: params.visitTypeLabelHe ?? null,
    visit_date: params.visitDate,
    header_fields: headerFields,
    local_status: "LOCAL_IN_PROGRESS",
    catalog_version: params.catalogVersion ?? null,
    organization_profile_snapshot:
      params.organizationProfileSnapshot ?? null,
  });
}

export type SyncNewVisitReportToServerResult =
  | { ok: true; serverReportId: string }
  | { ok: false; message: string };

/**
 * יצירה בשרת (אופציונלי במצב מקוון) - מעדכן `server_report_id` בדוח המקומי.
 * כשל לא מבטל את הדוח המקומי.
 */
export async function syncNewVisitReportToServer(
  localReport: LocalVisitReportRecord
): Promise<SyncNewVisitReportToServerResult> {
  const response = await apiFetch("/field-reports/visits", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: localReport.project_id,
      visit_type: localReport.visit_type,
      visit_date: localReport.visit_date,
    }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message =
      payload.error?.message
      || payload.message
      || payload.detail
      || "יצירת הדוח בשרת נכשלה";
    return { ok: false, message: String(message) };
  }

  const report = (await response.json()) as {
    id?: string;
    header_fields?: Record<string, unknown>;
  };
  const serverReportId = report.id ? String(report.id) : "";

  if (!serverReportId) {
    return { ok: false, message: "תשובת השרת חסרה מזהה דוח" };
  }

  const serverHeaderFields = report.header_fields;
  await saveLocalReport({
    ...localReport,
    server_report_id: serverReportId,
    header_fields:
      serverHeaderFields && Object.keys(serverHeaderFields).length > 0
        ? serverHeaderFields
        : localReport.header_fields,
  });

  return { ok: true, serverReportId };
}

export async function parseNewReportFormFromApi(): Promise<NewReportFormData> {
  const [projectsRes, typesRes] = await Promise.all([
    apiFetch("/projects"),
    apiFetch("/field-reports/visit-types"),
  ]);

  if (!projectsRes.ok || !typesRes.ok) {
    throw new Error("טעינת נתוני הטופס נכשלה");
  }

  const projectsPayload = await projectsRes.json();
  const typesPayload = await typesRes.json();

  const projectList = Array.isArray(projectsPayload)
    ? projectsPayload
    : projectsPayload.projects || [];

  const projects = (projectList as Array<Record<string, unknown>>)
    .map((project) => ({
      id: String(project.id ?? ""),
      project_name: String(project.project_name ?? project.id ?? "פרויקט"),
      prefill: projectPrefillSourceFromRecord(project),
    }))
    .filter((project) => project.id);

  const visitTypes = (
    (typesPayload.visit_types || []) as Array<Record<string, unknown>>
  )
    .map((visitType) => ({
      code: String(visitType.code ?? ""),
      label_he: String(visitType.label_he ?? visitType.code ?? ""),
    }))
    .filter((visitType) => visitType.code);

  return { projects, visitTypes };
}

/** טוען פרטי prefill מ-workspace כשאין בחבילה המקומית. */
export async function fetchProjectPrefill(
  projectId: string
): Promise<ProjectPrefillSource | null> {
  const response = await apiFetch(`/projects/${projectId}/workspace`);
  if (!response.ok) {
    return null;
  }

  const payload = (await response.json()) as {
    project?: Record<string, unknown>;
  };
  return projectPrefillSourceFromRecord(payload.project);
}
