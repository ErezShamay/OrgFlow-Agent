"use client";

import Button from "@/components/ui/Button";
import type { ClosePreview } from "@/lib/field-reports/close-preview";

export type { ClosePreview };

type FinishReportDialogProps = {
  open: boolean;
  loading: boolean;
  preview: ClosePreview | null;
  error: string;
  onCancel: () => void;
  onConfirm: () => void;
};

export default function FinishReportDialog({
  open,
  loading,
  preview,
  error,
  onCancel,
  onConfirm,
}: FinishReportDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="presentation"
      onClick={onCancel}
    >
      <div
        className="w-full max-w-md space-y-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-900"
        role="dialog"
        aria-modal="true"
        aria-labelledby="finish-report-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="finish-report-title" className="text-lg font-semibold">
          סיום דוח
        </h2>

        <p className="text-sm text-zinc-600 dark:text-zinc-300">
          הדוח יעבור למצב <strong>סגור</strong> ויופק PDF על המכשיר (כותרת
          מצילום פרופיל הארגון שנשמר בפתיחת הדוח). ניתן לערוך שוב ולעדכן PDF
          לפני שליחה לליבה.
        </p>

        {loading ? (
          <p className="text-sm text-zinc-500">בודק את הדוח...</p>
        ) : null}

        {!loading && preview?.warnings.length ? (
          <ul className="space-y-2 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:bg-amber-950/40 dark:text-amber-100">
            {preview.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        ) : null}

        {!loading && preview && !preview.warnings.length ? (
          <p className="text-sm text-emerald-800 dark:text-emerald-300">
            {preview.line_count} שורות - אין אזהרות לפני סגירה.
          </p>
        ) : null}

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        {!loading && preview?.blocking_errors?.length ? (
          <ul className="space-y-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-900 dark:bg-red-950/40 dark:text-red-100">
            {preview.blocking_errors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        ) : null}

        <div className="flex flex-wrap justify-end gap-2">
          <Button
            variant="secondary"
            type="button"
            disabled={loading}
            onClick={onCancel}
          >
            ביטול
          </Button>
          <Button
            type="button"
            disabled={loading || Boolean(preview?.blocking_errors?.length)}
            onClick={onConfirm}
          >
            {loading ? "סוגר..." : "אשר וסגור דוח"}
          </Button>
        </div>
      </div>
    </div>
  );
}
