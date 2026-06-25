"use client";

import GenerateVisitReportPdfButton from "@/components/field-reports/GenerateVisitReportPdfButton";
import Button from "@/components/ui/Button";
import {
  isVisitReportFinalizeComplete,
  isVisitReportFinalizeFailed,
  isVisitReportFinalizing,
} from "@/lib/field-reports/finalize-status-labels";
import type { VisitReportPdfDownloadSource } from "@/lib/field-reports/pdf/generate-visit-report-pdf";
import type { PdfVisitReport } from "@/lib/field-reports/pdf/types";
import { serverVisitReportId } from "@/lib/field-reports/visit-report-view";
import { downloadFieldVisitReportPdf } from "@/lib/deliverable-reports/api";

export type VisitReportPdfActionsReport = PdfVisitReport & {
  is_editable: boolean;
  status: string;
  is_published?: boolean;
  server_report_id?: string | null;
  client_report_uuid?: string;
};

const PDF_ACTION_STATUSES = new Set([
  "CLOSED",
  "PENDING_UPLOAD",
  "LOCKED",
  "FINALIZING",
  "FINALIZED",
  "FINALIZE_FAILED",
  "PUBLISHED",
]);

export function shouldShowVisitReportPdfActions(
  report: Pick<VisitReportPdfActionsReport, "is_editable" | "status">,
  isReopenedForEdit: boolean
): boolean {
  if (report.is_editable && isReopenedForEdit) {
    return true;
  }

  return !report.is_editable && PDF_ACTION_STATUSES.has(report.status);
}

type VisitReportPdfActionsProps = {
  report: VisitReportPdfActionsReport;
  isReopenedForEdit: boolean;
  hasLocalPdf: boolean;
  canFinalize?: boolean;
  isOnline?: boolean;
  className?: string;
  /** Stack actions vertically for narrow screens (e.g. mobile footer). */
  stacked?: boolean;
  onCacheChange: (hasLocal: boolean) => void;
  onSetNotice: (message: string) => void;
  onSetError: (message: string) => void;
  onFinalizeStart?: () => void;
  onFinalizeComplete?: () => void;
};

export default function VisitReportPdfActions({
  report,
  isReopenedForEdit,
  hasLocalPdf,
  canFinalize = false,
  isOnline = true,
  className = "",
  stacked = false,
  onCacheChange,
  onSetNotice,
  onSetError,
  onFinalizeStart,
  onFinalizeComplete,
}: VisitReportPdfActionsProps) {
  const serverReportId = serverVisitReportId(report);
  const isFinalizing = isVisitReportFinalizing(report.status);
  const isFinalized = isVisitReportFinalizeComplete(report.status);
  const isFinalizeFailed = isVisitReportFinalizeFailed(report.status);
  const canDownloadArchivedPdf = Boolean(
    (report.is_published || isFinalized) && serverReportId
  );
  const showGeneratePdfButton =
    !isFinalizing && (!isFinalized || !canDownloadArchivedPdf);
  const actionButtonClassName = stacked
    ? "min-h-12 w-full sm:w-auto"
    : "min-h-12";

  if (report.is_editable && isReopenedForEdit) {
    return (
      <div className={`space-y-1.5 ${className}`}>
        <GenerateVisitReportPdfButton
          report={report}
          variant="secondary"
          className={actionButtonClassName}
          forceRegenerate
          serverReportId={serverReportId}
          reportStatus={report.status}
          canFinalize={canFinalize}
          isOnline={isOnline}
          clientReportUuid={report.client_report_uuid}
          onCacheChange={onCacheChange}
          onFinalizeStart={onFinalizeStart}
          onFinalizeComplete={() => {
            onFinalizeComplete?.();
            onSetNotice(
              "ה-PDF עודכן והדוח נשלח לעיבוד. המייל יישלח אוטומטית בסיום."
            );
            onSetError("");
          }}
          onFinalizeError={(message) => {
            onSetError(message);
            onSetNotice("");
          }}
          onComplete={() => {
            onCacheChange(true);
            if (!canFinalize || !isOnline || !serverReportId) {
              onSetNotice(
                "ה-PDF עודכן לפי השינויים האחרונים, נשמר במכשיר והורד."
              );
            }
            onSetError("");
          }}
          onError={(message) => {
            onSetError(message);
            onSetNotice("");
          }}
        />
        <span className="text-sm text-zinc-600">
          לפני עדכון תוצג תצוגה מקדימה לאישור - נשמרת גרסה אחרונה בלבד במכשיר.
        </span>
      </div>
    );
  }

  if (!shouldShowVisitReportPdfActions(report, isReopenedForEdit)) {
    return null;
  }

  return (
    <div className={`space-y-2 pt-1 ${className}`}>
      {isFinalizing ? (
        <p className="text-sm text-sky-800 dark:text-sky-300">
          מעלה ומעבד דוח... המייל יישלח אוטומטית בסיום.
        </p>
      ) : null}
      {isFinalized ? (
        <p className="text-sm text-emerald-700 dark:text-emerald-300">
          הדוח נשלח בהצלחה לדיירים ולמשויכים לפרויקט.
        </p>
      ) : null}
      {isFinalizeFailed ? (
        <p className="text-sm text-red-600">
          עיבוד הדוח נכשל. נסה להפיק PDF מחדש.
        </p>
      ) : null}

      <div
        className={
          stacked
            ? "flex flex-col items-stretch gap-2.5 sm:flex-row sm:flex-wrap sm:items-center"
            : "flex flex-wrap items-center gap-2.5"
        }
      >
        {canDownloadArchivedPdf ? (
          <Button
            type="button"
            className={actionButtonClassName}
            onClick={() => {
              void downloadFieldVisitReportPdf(
                serverReportId!,
                report.project_name
                  ? `דוח-מפקח-${report.project_name}-${report.visit_date}.pdf`
                  : undefined
              )
                .then(() => {
                  onSetNotice("ה-PDF הורד מהארכיון בשרת.");
                  onSetError("");
                })
                .catch((err: unknown) => {
                  onSetError(
                    err instanceof Error
                      ? err.message
                      : "הורדת ה-PDF מהארכיון נכשלה"
                  );
                  onSetNotice("");
                });
            }}
          >
            הורד PDF מהארכיון
          </Button>
        ) : null}
        {showGeneratePdfButton ? (
          <GenerateVisitReportPdfButton
            report={report}
            className={actionButtonClassName}
            serverReportId={serverReportId}
            reportStatus={report.status}
            canFinalize={canFinalize}
            isOnline={isOnline}
            clientReportUuid={report.client_report_uuid}
            onCacheChange={onCacheChange}
            onFinalizeStart={onFinalizeStart}
            onFinalizeComplete={() => {
              onFinalizeComplete?.();
              onSetNotice(
                "הדוח נשלח בהצלחה לדיירים ולמשויכים לפרויקט."
              );
              onSetError("");
            }}
            onFinalizeError={(message) => {
              onSetError(message);
              onSetNotice("");
            }}
            onComplete={(source: VisitReportPdfDownloadSource) => {
              onCacheChange(true);
              if (source === "cache") {
                onSetNotice(
                  "ה-PDF הורד מהעותק השמור במכשיר (ללא רשת)."
                );
              } else if (!canFinalize || !isOnline || !serverReportId) {
                onSetNotice("ה-PDF הופק, נשמר במכשיר והורד.");
              }
              onSetError("");
            }}
            onError={(message) => {
              onSetError(message);
              onSetNotice("");
            }}
          />
        ) : null}
        {hasLocalPdf ? (
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-200">
            PDF שמור במכשיר
          </span>
        ) : null}
        {!isFinalized ? (
          <span className="text-sm text-zinc-600">
            {hasLocalPdf && canFinalize && isOnline
              ? "הפק PDF מציג תצוגה מקדימה, שולח לבעלי עניין ומפעיל עיבוד AI במערכת."
              : hasLocalPdf
                ? "ניתן להוריד שוב את ה-PDF גם ללא רשת."
                : "לפני הפקה תוצג תצוגה מקדימה לאישור; לאחר אישור הדוח יעובד, יישלח לבעלי עניין ויופעלו האוטומציות במערכת."}
          </span>
        ) : null}
      </div>
    </div>
  );
}
