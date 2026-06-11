import {
  resolveFieldReportDataSource,
  type FieldReportDataSource,
  type FieldReportNetworkSnapshot,
} from "@/lib/field-reports/data-source";
import type {
  LocalVisitReportLine,
  LocalVisitReportRecord,
} from "@/lib/field-reports/repositories/reports-repository";
import {
  getLocalReport,
  getLocalReportByServerId,
} from "@/lib/field-reports/repositories/reports-repository";
import { apiFetch } from "@/lib/api/client";

export type VisitReportLineView = {
  id: string;
  sort_order: number;
  description?: string | null;
  catalog_warning?: string | null;
  location?: string | null;
  trade?: string | null;
  status?: string | null;
  notes?: string | null;
  severity?: string | null;
  standard_ref?: string | null;
  issue_id?: string | null;
  has_catalog_issue?: boolean;
  has_photo?: boolean;
  photo_url?: string | null;
  photo_ids?: string[];
  photos?: Array<{ id: string; url: string }>;
  group_key?: string | null;
  group_label_he?: string | null;
  block_id?: string | null;
  linked_issue_id?: string | null;
};

/** צורת דוח ל-UI (עמוד דוח + עורך) - תואם לתשובת API עם שדות מקומיים. */
export type VisitReportView = {
  id: string;
  client_report_uuid: string;
  server_report_id?: string | null;
  project_id?: string;
  project_name?: string;
  visit_type: string;
  visit_type_label_he: string;
  status_label_he: string;
  visit_date: string;
  status: string;
  header_fields: Record<string, unknown>;
  catalog_version?: string | null;
  current_catalog_version?: string | null;
  catalog_sync?: {
    is_current?: boolean;
    message?: string | null;
  };
  closed_at?: string | null;
  organization_profile_snapshot?: Record<string, unknown> | null;
  lines: VisitReportLineView[];
  line_count?: number;
  is_editable: boolean;
  can_reopen?: boolean;
  can_send_to_core?: boolean;
  was_closed?: boolean;
};

const LOCAL_STATUS_UI: Record<
  LocalVisitReportRecord["local_status"],
  {
    status: string;
    status_label_he: string;
    is_editable: boolean;
    can_reopen: boolean;
    can_send_to_core: boolean;
  }
> = {
  LOCAL_DRAFT: {
    status: "IN_PROGRESS",
    status_label_he: "טיוטה במכשיר",
    is_editable: true,
    can_reopen: false,
    can_send_to_core: false,
  },
  LOCAL_IN_PROGRESS: {
    status: "IN_PROGRESS",
    status_label_he: "בעבודה",
    is_editable: true,
    can_reopen: false,
    can_send_to_core: false,
  },
  LOCAL_CLOSED: {
    status: "CLOSED",
    status_label_he: "סגור (מקומי)",
    is_editable: false,
    can_reopen: false,
    can_send_to_core: false,
  },
};

export function localLineToView(line: LocalVisitReportLine): VisitReportLineView {
  const lineId = line.client_line_uuid || line.id;

  return {
    id: lineId,
    sort_order: line.sort_order ?? 0,
    description: line.description ?? null,
    location: line.location ?? null,
    trade: line.trade ?? null,
    status: line.status ?? null,
    notes: line.notes ?? null,
    severity: line.severity ?? null,
    standard_ref: line.standard_ref ?? null,
    issue_id: line.issue_id ?? null,
    has_catalog_issue: Boolean(line.issue_id),
    has_photo: line.has_photo,
    photo_ids: line.photo_ids,
    catalog_warning: null,
    group_key: line.group_key ?? null,
    group_label_he: line.group_label_he ?? null,
    block_id: line.block_id ?? null,
    linked_issue_id: line.linked_issue_id ?? null,
  };
}

export function localVisitReportToView(
  record: LocalVisitReportRecord
): VisitReportView {
  const statusUi = LOCAL_STATUS_UI[record.local_status];
  const lines = [...record.lines]
    .sort((left, right) => (left.sort_order ?? 0) - (right.sort_order ?? 0))
    .map(localLineToView);

  return {
    id: record.client_report_uuid,
    client_report_uuid: record.client_report_uuid,
    server_report_id: record.server_report_id ?? null,
    project_id: record.project_id,
    project_name: record.project_name ?? undefined,
    visit_type: record.visit_type,
    visit_type_label_he: record.visit_type_label_he || record.visit_type,
    visit_date: record.visit_date,
    status: statusUi.status,
    status_label_he: statusUi.status_label_he,
    header_fields: record.header_fields,
    catalog_version: record.catalog_version ?? null,
    lines,
    line_count: lines.length,
    is_editable: statusUi.is_editable,
    can_reopen: statusUi.can_reopen,
    can_send_to_core: statusUi.can_send_to_core,
    was_closed: Boolean(record.closed_at),
    closed_at: record.closed_at ?? null,
    organization_profile_snapshot:
      record.organization_profile_snapshot ?? null,
  };
}

/** מזהה לנתיב `/field-reports/{id}` - UUID מקומי או מזהה שרת. */
export async function resolveLocalVisitReport(
  routeId: string
): Promise<LocalVisitReportRecord | null> {
  if (!routeId) {
    return null;
  }

  const byClient = await getLocalReport(routeId);
  if (byClient) {
    return byClient;
  }

  return getLocalReportByServerId(routeId);
}

/**
 * מזהה שרת לקריאות API - גם כש-`routeId` הוא UUID (מפתח Supabase).
 * לא משתמשים ב-`isClientUuid`: מזהה מקומי ומזהה שרת יכולים להיות באותו פורמט.
 */
export function resolveVisitReportApiId(
  routeId: string,
  localRecord: LocalVisitReportRecord | null
): string | null {
  if (localRecord?.server_report_id) {
    return localRecord.server_report_id;
  }

  if (!routeId) {
    return null;
  }

  if (
    localRecord
    && localRecord.client_report_uuid === routeId
  ) {
    return null;
  }

  return routeId;
}

export function serverVisitReportId(
  report: Pick<VisitReportView, "id" | "server_report_id" | "client_report_uuid">
): string | null {
  if (report.server_report_id) {
    return report.server_report_id;
  }

  const clientUuid = report.client_report_uuid;
  if (clientUuid && report.id === clientUuid) {
    return null;
  }

  return report.id || null;
}

export function clientVisitReportUuid(
  report: Pick<VisitReportView, "id" | "client_report_uuid">
): string {
  return report.client_report_uuid || report.id;
}

export type LoadVisitReportResult = {
  report: VisitReportView;
  source: "local" | "remote";
  localRecord: LocalVisitReportRecord | null;
  dataSource: FieldReportDataSource;
};

export async function loadVisitReportForPage(
  routeId: string,
  network: FieldReportNetworkSnapshot
): Promise<LoadVisitReportResult> {
  const localRecord = await resolveLocalVisitReport(routeId);
  const serverReportIdForContext = resolveVisitReportApiId(
    routeId,
    localRecord
  );

  const dataSource = resolveFieldReportDataSource(network, {
    hasLocalReport: Boolean(localRecord),
    serverReportId: serverReportIdForContext,
  });

  if (
    localRecord
    && (dataSource.useLocalReports || !dataSource.canCallVisitReportApi)
  ) {
    return {
      report: localVisitReportToView(localRecord),
      source: "local",
      localRecord,
      dataSource,
    };
  }

  const apiReportId = resolveVisitReportApiId(routeId, localRecord);

  if (apiReportId && dataSource.canCallVisitReportApi) {
    const response = await apiFetch(`/field-reports/visits/${apiReportId}`);

    if (!response.ok) {
      throw new Error("טעינת הדוח נכשלה");
    }

    const remote = (await response.json()) as VisitReportView;
    return {
      report: {
        ...remote,
        client_report_uuid:
          localRecord?.client_report_uuid
          ?? remote.client_report_uuid
          ?? clientVisitReportUuid(remote),
        server_report_id: apiReportId,
      },
      source: "remote",
      localRecord,
      dataSource,
    };
  }

  if (localRecord) {
    return {
      report: localVisitReportToView(localRecord),
      source: "local",
      localRecord,
      dataSource,
    };
  }

  throw new Error("דוח לא נמצא");
}
