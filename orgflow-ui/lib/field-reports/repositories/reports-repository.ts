import {
  FIELD_REPORT_STORES,
  type LocalReportStatus,
  type LocalSyncStatus,
  type LocalVisitReportLine,
  type LocalVisitReportRecord,
} from "@/lib/field-reports/db/schema";
import { getFieldReportDatabase } from "@/lib/field-reports/db/field-report-db";
import {
  createClientLineUuid,
  createClientReportUuid,
} from "@/lib/field-reports/ids";

export type { LocalVisitReportLine, LocalVisitReportRecord };

export type SaveLocalReportInput = {
  client_report_uuid?: string;
  server_report_id?: string | null;
  organization_id: string;
  user_id?: string | null;
  project_id: string;
  project_name?: string | null;
  visit_type: string;
  visit_type_label_he?: string | null;
  visit_date: string;
  header_fields: Record<string, unknown>;
  lines?: LocalVisitReportLine[];
  local_status?: LocalReportStatus;
  sync_status?: LocalSyncStatus;
  catalog_version?: string | null;
  organization_profile_snapshot?: Record<string, unknown> | null;
  closed_at?: string | null;
};

export type UpsertLineInput = Partial<
  Omit<LocalVisitReportLine, "client_line_uuid">
> & {
  client_line_uuid?: string;
};

function nowIso() {
  return new Date().toISOString();
}

function normalizeLine(
  line: UpsertLineInput & { client_line_uuid?: string },
  fallbackSortOrder: number
): LocalVisitReportLine {
  const clientLineUuid = line.client_line_uuid || createClientLineUuid();

  return {
    id: line.id || clientLineUuid,
    client_line_uuid: clientLineUuid,
    server_line_id: line.server_line_id ?? null,
    sort_order: line.sort_order ?? fallbackSortOrder,
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
    linked_issue_id: line.linked_issue_id ?? null,
    has_photo: line.has_photo,
    photo_ids: line.photo_ids,
  };
}

function normalizeLines(
  lines: Array<UpsertLineInput & { client_line_uuid?: string }>
): LocalVisitReportLine[] {
  return lines.map((line, index) =>
    normalizeLine(line, index + 1)
  );
}

/**
 * שומר דוח מקומי (יצירה או עדכון מלא) ב-`reports` store.
 */
export async function saveLocalReport(
  input: SaveLocalReportInput
): Promise<LocalVisitReportRecord> {
  const clientReportUuid =
    input.client_report_uuid || createClientReportUuid();
  const existing = await getLocalReport(clientReportUuid);
  const timestamp = nowIso();

  const record: LocalVisitReportRecord = {
    client_report_uuid: clientReportUuid,
    server_report_id:
      input.server_report_id !== undefined
        ? input.server_report_id
        : existing?.server_report_id ?? null,
    organization_id: input.organization_id,
    user_id: input.user_id ?? existing?.user_id ?? null,
    project_id: input.project_id,
    project_name: input.project_name ?? existing?.project_name ?? null,
    visit_type: input.visit_type,
    visit_type_label_he:
      input.visit_type_label_he ?? existing?.visit_type_label_he ?? null,
    visit_date: input.visit_date,
    header_fields: input.header_fields,
    lines: input.lines
      ? normalizeLines(input.lines)
      : existing?.lines ?? [],
    local_status:
      input.local_status
      ?? existing?.local_status
      ?? "LOCAL_DRAFT",
    sync_status:
      input.sync_status ?? existing?.sync_status ?? "pending",
    catalog_version:
      input.catalog_version ?? existing?.catalog_version ?? null,
    organization_profile_snapshot:
      input.organization_profile_snapshot
      ?? existing?.organization_profile_snapshot
      ?? null,
    created_at: existing?.created_at ?? timestamp,
    updated_at: timestamp,
    closed_at:
      input.closed_at !== undefined
        ? input.closed_at
        : existing?.closed_at ?? null,
  };

  const database = await getFieldReportDatabase();
  await database.put(FIELD_REPORT_STORES.reports, record);
  return record;
}

export async function getLocalReport(
  clientReportUuid: string
): Promise<LocalVisitReportRecord | null> {
  if (!clientReportUuid) {
    return null;
  }

  const database = await getFieldReportDatabase();
  const record = await database.get(
    FIELD_REPORT_STORES.reports,
    clientReportUuid
  );
  return record ?? null;
}

export async function getLocalReportByServerId(
  serverReportId: string
): Promise<LocalVisitReportRecord | null> {
  if (!serverReportId) {
    return null;
  }

  const database = await getFieldReportDatabase();
  const matches = await database.getAllFromIndex(
    FIELD_REPORT_STORES.reports,
    "by-server-id",
    serverReportId
  );
  return matches[0] ?? null;
}

export async function listLocalReportsForOrganization(
  organizationId: string
): Promise<LocalVisitReportRecord[]> {
  if (!organizationId) {
    return [];
  }

  const database = await getFieldReportDatabase();
  return database.getAllFromIndex(
    FIELD_REPORT_STORES.reports,
    "by-organization",
    organizationId
  );
}

/**
 * מוסיף או מעדכן שורה בדוח - לפי `client_line_uuid`.
 */
export async function upsertLine(
  clientReportUuid: string,
  line: UpsertLineInput
): Promise<LocalVisitReportRecord | null> {
  const report = await getLocalReport(clientReportUuid);
  if (!report) {
    return null;
  }

  const clientLineUuid = line.client_line_uuid || createClientLineUuid();
  const lineIndex = report.lines.findIndex(
    (entry) => entry.client_line_uuid === clientLineUuid
  );
  const nextLine = normalizeLine(
    {
      ...(lineIndex >= 0 ? report.lines[lineIndex] : {}),
      ...line,
      client_line_uuid: clientLineUuid,
    },
    lineIndex >= 0
      ? (report.lines[lineIndex].sort_order ?? lineIndex + 1)
      : report.lines.length + 1
  );

  const lines = [...report.lines];
  if (lineIndex >= 0) {
    lines[lineIndex] = nextLine;
  } else {
    lines.push(nextLine);
  }

  return saveLocalReport({
    ...report,
    lines,
  });
}

/** מוחק שורה מדוח מקומי. */
export async function deleteLine(
  clientReportUuid: string,
  clientLineUuid: string
): Promise<LocalVisitReportRecord | null> {
  const report = await getLocalReport(clientReportUuid);
  if (!report) {
    return null;
  }

  const lines = report.lines.filter(
    (entry) => entry.client_line_uuid !== clientLineUuid
  );

  if (lines.length === report.lines.length) {
    return report;
  }

  return saveLocalReport({
    ...report,
    lines,
  });
}

export async function deleteLocalReport(
  clientReportUuid: string
): Promise<void> {
  if (!clientReportUuid) {
    return;
  }

  const database = await getFieldReportDatabase();
  await database.delete(
    FIELD_REPORT_STORES.reports,
    clientReportUuid
  );
}
