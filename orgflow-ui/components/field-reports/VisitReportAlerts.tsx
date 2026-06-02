"use client";

import Button from "@/components/ui/Button";

type VisitReportAlertsReport = {
  can_send_to_core?: boolean;
};

type VisitReportAlertsProps = {
  report: VisitReportAlertsReport;
  pdfNotice: string;
  pdfError: string;
  reopenError: string;
  sendNotice: string;
  showPendingSendState: boolean;
  pendingSendPhase: string;
  pendingSendError: string;
  localPendingSend: boolean;
  hasPendingSendFailure: boolean;
  onCancelPendingSend: () => void;
  onOpenSendDialog: () => void;
};

export default function VisitReportAlerts({
  report,
  pdfNotice,
  pdfError,
  reopenError,
  sendNotice,
  showPendingSendState,
  pendingSendPhase,
  pendingSendError,
  localPendingSend,
  hasPendingSendFailure,
  onCancelPendingSend,
  onOpenSendDialog,
}: VisitReportAlertsProps) {
  return (
    <>
      {pdfNotice ? (
        <p className="text-sm text-emerald-700 dark:text-emerald-300">{pdfNotice}</p>
      ) : null}
      {pdfError ? <p className="text-sm text-red-600">{pdfError}</p> : null}
      {reopenError ? <p className="text-sm text-red-600">{reopenError}</p> : null}
      {sendNotice ? (
        <p className="text-sm text-emerald-700 dark:text-emerald-300">{sendNotice}</p>
      ) : null}

      {showPendingSendState ? (
        <div className="space-y-1 text-sm text-sky-800 dark:text-sky-300">
          <p>הדוח ממתין לשליחה לליבה. לא ניתן לערוך עד לסיום ההעלאה.</p>
          {pendingSendPhase ? (
            <p className="text-sky-700 dark:text-sky-200">{pendingSendPhase}</p>
          ) : null}
          {pendingSendError ? (
            <p className="text-amber-800 dark:text-amber-200">{pendingSendError}</p>
          ) : null}
          {localPendingSend ? (
            <div className="pt-1">
              <Button
                variant="secondary"
                size="lg"
                className="min-h-12"
                onClick={onCancelPendingSend}
              >
                בטל המתנה לשליחה
              </Button>
            </div>
          ) : null}
        </div>
      ) : null}

      {hasPendingSendFailure ? (
        <div className="space-y-1 text-sm text-amber-800 dark:text-amber-200">
          <p>השליחה לליבה נכשלה. ניתן לערוך את הדוח או לנסות שליחה מחדש.</p>
          {pendingSendError ? <p>{pendingSendError}</p> : null}
          {report.can_send_to_core ? (
            <div className="pt-1">
              <Button
                variant="secondary"
                size="lg"
                className="min-h-12"
                onClick={onOpenSendDialog}
              >
                נסה שליחה מחדש
              </Button>
            </div>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
