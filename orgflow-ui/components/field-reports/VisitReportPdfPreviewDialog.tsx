"use client";

import Button from "@/components/ui/Button";

type VisitReportPdfPreviewDialogProps = {
  open: boolean;
  loading: boolean;
  confirming: boolean;
  previewUrl: string | null;
  error: string;
  isRegenerate?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

export default function VisitReportPdfPreviewDialog({
  open,
  loading,
  confirming,
  previewUrl,
  error,
  isRegenerate = false,
  onCancel,
  onConfirm,
}: VisitReportPdfPreviewDialogProps) {
  if (!open) {
    return null;
  }

  const busy = loading || confirming;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-2 sm:items-center sm:p-4"
      role="presentation"
      onClick={busy ? undefined : onCancel}
    >
      <div
        className="flex max-h-[92vh] w-full max-w-4xl flex-col gap-4 rounded-2xl border border-zinc-200 bg-white p-4 shadow-xl dark:border-zinc-700 dark:bg-zinc-900 sm:p-6"
        role="dialog"
        aria-modal="true"
        aria-labelledby="visit-report-pdf-preview-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="space-y-1">
          <h2
            id="visit-report-pdf-preview-title"
            className="text-lg font-semibold"
          >
            תצוגה מקדימה של הדוח
          </h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            {isRegenerate
              ? "בדקו שהעדכונים נראים נכון לפני שמירת ה-PDF והמשך העיבוד."
              : "בדקו שהדוח נראה נכון. לאחר אישור: שמירה במכשיר, שליחה לבעלי עניין ועיבוד הדוח במערכת."}
          </p>
        </div>

        <div className="min-h-[50vh] flex-1 overflow-hidden rounded-xl border border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-950/50 sm:min-h-[60vh]">
          {loading ? (
            <div className="flex h-full min-h-[50vh] items-center justify-center text-sm text-zinc-500 sm:min-h-[60vh]">
              מכין תצוגה מקדימה...
            </div>
          ) : null}

          {!loading && previewUrl ? (
            <iframe
              src={previewUrl}
              title="תצוגה מקדימה של דוח PDF"
              className="h-full min-h-[50vh] w-full sm:min-h-[60vh]"
            />
          ) : null}

          {!loading && !previewUrl && !error ? (
            <div className="flex h-full min-h-[50vh] items-center justify-center text-sm text-zinc-500 sm:min-h-[60vh]">
              לא ניתן להציג תצוגה מקדימה
            </div>
          ) : null}
        </div>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <div className="flex flex-wrap justify-end gap-2">
          <Button
            variant="secondary"
            type="button"
            disabled={busy}
            onClick={onCancel}
          >
            ביטול
          </Button>
          <Button
            type="button"
            disabled={busy || !previewUrl}
            onClick={onConfirm}
          >
            {confirming
              ? "מפיק ומעבד..."
              : isRegenerate
                ? "אשר ועדכן PDF"
                : "אשר והפק PDF"}
          </Button>
        </div>
      </div>
    </div>
  );
}
