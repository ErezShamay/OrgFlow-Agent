import type { LocalVisitReportRecord } from "@/lib/field-reports/repositories/reports-repository";

/** גוף `PUT /field-reports/visits/sync` - ממופה מדוח מקומי. */
export type VisitReportSyncRequestBody = {
  client_report_uuid: string;
  project_id: string;
  visit_type: string;
  visit_date: string;
  header_fields: Record<string, unknown>;
  catalog_version?: string | null;
  organization_profile_snapshot?: Record<string, unknown> | null;
  lines: Array<{
    client_line_uuid: string;
    sort_order?: number | null;
    location?: string | null;
    trade?: string | null;
    status?: string | null;
    description?: string | null;
    notes?: string | null;
    severity?: string | null;
    standard_ref?: string | null;
    issue_id?: string | null;
    group_key?: string | null;
    group_label_he?: string | null;
    block_id?: string | null;
  }>;
};

export function buildVisitReportSyncBody(
  record: LocalVisitReportRecord
): VisitReportSyncRequestBody {
  return {
    client_report_uuid: record.client_report_uuid,
    project_id: record.project_id,
    visit_type: record.visit_type,
    visit_date: record.visit_date,
    header_fields: record.header_fields,
    catalog_version: record.catalog_version ?? null,
    organization_profile_snapshot:
      record.organization_profile_snapshot ?? null,
    lines: record.lines.map((line) => ({
      client_line_uuid: line.client_line_uuid,
      sort_order: line.sort_order ?? null,
      location: line.location ?? null,
      trade: line.trade ?? null,
      status: line.status ?? null,
      description: line.description ?? null,
      notes: line.notes ?? null,
      severity: line.severity ?? null,
      standard_ref: line.standard_ref ?? null,
      issue_id: line.issue_id ?? null,
      group_key: line.group_key ?? null,
      group_label_he: line.group_label_he ?? null,
      block_id: line.block_id ?? null,
    })),
  };
}
