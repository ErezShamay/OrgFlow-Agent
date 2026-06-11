import { getProjectVisitIssueDiff } from "@/lib/quality-issues/api";

import {
  buildLineIssueMarkerMapFromVisitDiff,
  type PdfLineIssueMarkerMap,
} from "./pdf-issue-markers";
import type { PdfVisitReport } from "./types";

const CLOSED_VISIT_STATUSES_FOR_PDF_MARKERS = new Set([
  "CLOSED",
  "SENT",
  "PENDING_UPLOAD",
  "LOCKED",
]);

export async function resolveVisitPdfIssueMarkers(
  report: Pick<
    PdfVisitReport,
    "project_id" | "server_report_id" | "id" | "status"
  >
): Promise<PdfLineIssueMarkerMap | undefined> {
  const projectId = report.project_id?.trim();
  const reportId = report.server_report_id?.trim() || report.id?.trim();
  const status = (report.status || "").trim().toUpperCase();

  if (!projectId || !reportId) {
    return undefined;
  }

  if (!CLOSED_VISIT_STATUSES_FOR_PDF_MARKERS.has(status)) {
    return undefined;
  }

  try {
    const diff = await getProjectVisitIssueDiff(projectId, reportId);
    const map = buildLineIssueMarkerMapFromVisitDiff(diff);
    return map.size > 0 ? map : undefined;
  } catch {
    return undefined;
  }
}
