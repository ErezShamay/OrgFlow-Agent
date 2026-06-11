import { buildPdfFilename } from "@/lib/field-reports/pdf/build-doc-definition";
import {
  generateVisitReportPdf,
  type VisitReportPdfDownloadSource,
} from "@/lib/field-reports/pdf/generate-visit-report-pdf";
import {
  hasVisitReportPdfLocally,
  loadVisitReportPdfLocally,
  saveVisitReportPdfLocally,
} from "@/lib/field-reports/pdf/visit-report-pdf-store";
import type { VisitReportPdfInput } from "@/lib/field-reports/pdf/types";
import {
  getLocalReport,
  saveLocalReport,
  type LocalVisitReportRecord,
} from "@/lib/field-reports/repositories/reports-repository";
import { enqueueSyncQueueRecord } from "@/lib/field-reports/repositories/sync-queue-repository";
import {
  clientVisitReportUuid,
  localVisitReportToView,
  type VisitReportView,
} from "@/lib/field-reports/visit-report-view";

export type FinishLocalVisitReportResult = {
  record: LocalVisitReportRecord;
  view: VisitReportView;
  pdfSource: VisitReportPdfDownloadSource | "skipped";
};

function nowIso() {
  return new Date().toISOString();
}

/**
 * סוגר דוח מקומי - `LOCAL_CLOSED`, `closed_at`, `sync_status=pending` (§6 ב.6).
 */
export async function closeLocalVisitReport(
  clientReportUuid: string,
  closedAt: string = nowIso()
): Promise<LocalVisitReportRecord> {
  const existing = await getLocalReport(clientReportUuid);
  if (!existing) {
    throw new Error("דוח מקומי לא נמצא");
  }

  if (existing.local_status === "LOCAL_CLOSED") {
    return existing;
  }

  const record = await saveLocalReport({
    client_report_uuid: clientReportUuid,
    organization_id: existing.organization_id,
    server_report_id: existing.server_report_id,
    user_id: existing.user_id,
    project_id: existing.project_id,
    project_name: existing.project_name,
    visit_type: existing.visit_type,
    visit_type_label_he: existing.visit_type_label_he,
    visit_date: existing.visit_date,
    header_fields: existing.header_fields,
    lines: existing.lines,
    catalog_version: existing.catalog_version,
    organization_profile_snapshot: existing.organization_profile_snapshot,
    local_status: "LOCAL_CLOSED",
    sync_status: "pending",
    closed_at: closedAt,
  });

  await enqueueSyncQueueRecord({
    client_report_uuid: clientReportUuid,
    organization_id: record.organization_id,
    user_id: record.user_id,
    server_report_id: record.server_report_id,
    sync_phase: "queued",
    sync_status: "pending",
  });

  return record;
}

/**
 * סוגר דוח מקומי, מפיק PDF מהעותק המקומי ושומר ב-blobs (דרך visit-report-pdf-store).
 */
export async function finishLocalVisitReportWithPdf(
  pdfInput: VisitReportPdfInput
): Promise<FinishLocalVisitReportResult> {
  const clientReportUuid = clientVisitReportUuid({
    id: pdfInput.report.id,
    client_report_uuid: pdfInput.report.id,
  });
  const record = await closeLocalVisitReport(clientReportUuid);
  const view = localVisitReportToView(record);
  const reportForPdf: VisitReportPdfInput["report"] = {
    ...pdfInput.report,
    id: view.id,
    project_name: view.project_name ?? pdfInput.report.project_name,
    visit_type: view.visit_type,
    visit_type_label_he: view.visit_type_label_he,
    visit_date: view.visit_date,
    header_fields: view.header_fields,
    lines: view.lines,
    organization_profile_snapshot:
      (view.organization_profile_snapshot
        ?? pdfInput.report.organization_profile_snapshot) as VisitReportPdfInput["report"]["organization_profile_snapshot"],
  };

  const filename = buildPdfFilename(reportForPdf);
  const cached = await loadVisitReportPdfLocally(view.id);
  if (cached?.blob) {
    return { record, view, pdfSource: "cache" };
  }

  const blob = await generateVisitReportPdf({
    ...pdfInput,
    report: reportForPdf,
  });
  await saveVisitReportPdfLocally(
    view.id,
    blob,
    filename,
    pdfInput.generatedAt ?? new Date()
  );

  const hasPdf = await hasVisitReportPdfLocally(view.id);
  if (!hasPdf) {
    throw new Error("שמירת PDF במכשיר נכשלה");
  }

  return { record, view, pdfSource: "generated" };
}
