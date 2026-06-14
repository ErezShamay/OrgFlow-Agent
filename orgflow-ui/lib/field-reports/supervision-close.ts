import {
  checklistCloseErrorsToMessages,
  validateChecklistForClose,
  type ChecklistCloseError,
} from "@/lib/field-reports/checklist-close-validation";
import { applySupervisionDefectLinesToReport } from "@/lib/field-reports/checklist-defect-to-line";
import { normalizeHeaderFields } from "@/lib/field-reports/header-fields";
import type { ClosePreview, ReportLineForClose } from "@/lib/field-reports/close-preview";
import {
  getLocalReport,
  saveLocalReport,
  type LocalVisitReportRecord,
} from "@/lib/field-reports/repositories/reports-repository";
import { isSupervisionChecklistReport } from "@/lib/field-reports/supervision-checklist-builder";
import type { SupervisionChecklistBlock } from "@/lib/field-reports/schema/types";

export class SupervisionCloseValidationError extends Error {
  errors: ChecklistCloseError[];

  constructor(errors: ChecklistCloseError[]) {
    super(checklistCloseErrorsToMessages(errors).join("\n"));
    this.name = "SupervisionCloseValidationError";
    this.errors = errors;
  }
}

export function findSupervisionChecklistBlock(
  headerFields: Record<string, unknown>,
  visitType: string
): SupervisionChecklistBlock | null {
  const normalized = normalizeHeaderFields(headerFields, visitType);
  const match = normalized.blocks.find(
    (block): block is SupervisionChecklistBlock =>
      block.kind === "supervision_checklist"
  );
  return match ?? null;
}

export function buildSupervisionClosePreview(params: {
  header_fields: Record<string, unknown>;
  visit_type: string;
  lines: ReportLineForClose[];
}): ClosePreview {
  const block = findSupervisionChecklistBlock(
    params.header_fields,
    params.visit_type
  );

  if (!block) {
    return {
      line_count: params.lines.length,
      empty_line_count: 0,
      empty_line_ids: [],
      catalog_warning_count: 0,
      warnings: ["לא נמצא בלוק צ'קליסט supervision."],
      blocking_errors: ["לא נמצא בלוק צ'קליסט supervision."],
    };
  }

  const validation = validateChecklistForClose(block);
  const defectCount = block.items.filter(
    (item) => item.status === "DEFECT"
  ).length;
  const uncheckedCount = block.items.filter(
    (item) => item.status === "UNCHECKED"
  ).length;

  const warnings: string[] = [
    `${block.items.length} פריטי צ'קליסט · ${defectCount} ליקויים · ${uncheckedCount} לא נבדקו`,
  ];

  const blocking_errors = validation.ok
    ? []
    : checklistCloseErrorsToMessages(validation.errors);

  return {
    line_count: params.lines.length,
    empty_line_count: 0,
    empty_line_ids: [],
    catalog_warning_count: 0,
    warnings,
    blocking_errors,
  };
}

export function isSupervisionVisitReport(
  headerFields: Record<string, unknown> | null | undefined,
  visitType: string
): boolean {
  if (!headerFields) {
    return false;
  }

  const normalized = normalizeHeaderFields(headerFields, visitType);
  return isSupervisionChecklistReport(normalized.blocks);
}

/**
 * מוודא צ'קליסט, מסנכרן שורות DEFECT, ושומר לפני סגירה (§8.2, §9).
 */
export async function prepareSupervisionReportForClose(
  clientReportUuid: string
): Promise<LocalVisitReportRecord> {
  const existing = await getLocalReport(clientReportUuid);
  if (!existing) {
    throw new Error("דוח מקומי לא נמצא");
  }

  const block = findSupervisionChecklistBlock(
    existing.header_fields,
    existing.visit_type
  );

  if (!block) {
    throw new Error("לא נמצא בלוק צ'קליסט supervision");
  }

  const validation = validateChecklistForClose(block);
  if (!validation.ok) {
    throw new SupervisionCloseValidationError(validation.errors);
  }

  const synced = applySupervisionDefectLinesToReport(existing);

  return saveLocalReport({
    client_report_uuid: synced.client_report_uuid,
    organization_id: synced.organization_id,
    server_report_id: synced.server_report_id,
    user_id: synced.user_id,
    project_id: synced.project_id,
    project_name: synced.project_name,
    visit_type: synced.visit_type,
    visit_type_label_he: synced.visit_type_label_he,
    visit_date: synced.visit_date,
    header_fields: synced.header_fields,
    lines: synced.lines,
    local_status: synced.local_status,
    sync_status: synced.sync_status,
    catalog_version: synced.catalog_version,
    organization_profile_snapshot: synced.organization_profile_snapshot,
    closed_at: synced.closed_at,
  });
}
