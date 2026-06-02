"use client";

import Button from "@/components/ui/Button";

type VisitReportPrimaryActionsReport = {
  is_editable: boolean;
  can_reopen?: boolean;
  can_send_to_core?: boolean;
};

type VisitReportPrimaryActionsProps = {
  report: VisitReportPrimaryActionsReport;
  isOnline: boolean;
  isReopenedForEdit: boolean;
  reopenLoading: boolean;
  hasLocalPdf: boolean;
  compact?: boolean;
  onOpenFinishDialog: () => void;
  onConfirmReopenReport: () => void;
  onOpenSendDialog: () => void;
};

export default function VisitReportPrimaryActions({
  report,
  isOnline,
  isReopenedForEdit,
  reopenLoading,
  hasLocalPdf,
  compact = false,
  onOpenFinishDialog,
  onConfirmReopenReport,
  onOpenSendDialog,
}: VisitReportPrimaryActionsProps) {
  if (report.is_editable) {
    return (
      <div className="flex flex-wrap items-center gap-2.5 pt-1">
        <Button
          size="lg"
          className="min-h-12"
          onClick={onOpenFinishDialog}
          disabled={!isOnline}
        >
          {isReopenedForEdit ? "סגור דוח שוב" : "סיום דוח"}
        </Button>
        {!isOnline ? (
          <span className="self-center text-sm text-amber-800">סגירה דורשת רשת</span>
        ) : null}
      </div>
    );
  }

  if (!report.can_reopen) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2.5 pt-1">
      <Button
        size="lg"
        className="min-h-12"
        onClick={onConfirmReopenReport}
        disabled={!isOnline || reopenLoading}
      >
        {reopenLoading ? "פותח לעריכה..." : "ערוך שוב"}
      </Button>
      {!compact && report.can_send_to_core ? (
        <Button
          variant="secondary"
          size="lg"
          className="min-h-12"
          onClick={onOpenSendDialog}
          disabled={!hasLocalPdf}
        >
          שלח לליבה
        </Button>
      ) : null}
      {!isOnline ? (
        <span className="self-center text-sm text-amber-800">
          עריכה מחדש דורשת רשת
        </span>
      ) : null}
      {!compact && !hasLocalPdf && report.can_send_to_core ? (
        <span className="text-sm text-amber-800">הפק PDF לפני שליחה לליבה</span>
      ) : null}
    </div>
  );
}
