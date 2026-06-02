import { clearEditSession } from "@/lib/field-reports/edit-session";
import { clearOfflinePrepBundle } from "@/lib/field-reports/offline-store";
import {
  clearAllReportMetadataDrafts,
} from "@/lib/field-reports/report-metadata-draft";
import {
  clearAllPendingSendRequests,
} from "@/lib/field-reports/send-queue";

export function clearFieldReportLocalState(organizationId: string) {
  if (typeof window === "undefined" || !organizationId) {
    return;
  }

  clearOfflinePrepBundle(organizationId);
  clearAllReportMetadataDrafts(organizationId);
  clearAllPendingSendRequests(organizationId);
  clearEditSession(organizationId);
}
