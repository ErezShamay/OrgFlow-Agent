"use client";

import Button from "@/components/ui/Button";

type SendToCoreDialogProps = {
  open: boolean;
  loading: boolean;
  offline: boolean;
  hasLocalPdf: boolean;
  error: string;
  onCancel: () => void;
  onConfirm: () => void;
};

export default function SendToCoreDialog({
  open,
  loading,
  offline,
  hasLocalPdf,
  error,
  onCancel,
  onConfirm,
}: SendToCoreDialogProps) {
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
        aria-labelledby="send-to-core-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="send-to-core-title" className="text-lg font-semibold">
          שלח לליבה
        </h2>

        <p className="text-sm text-zinc-600 dark:text-zinc-300">
          הדוח יועלה למערכת הליבה ויעבור למצב{" "}
          <strong>נעול</strong>.{" "}
          <strong className="text-red-700 dark:text-red-400">
            לא ניתן לערוך את הדוח לאחר שליחה מוצלחת.
          </strong>
        </p>

        {!hasLocalPdf ? (
          <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:bg-amber-950/40 dark:text-amber-100">
            יש להפיק PDF במכשיר לפני שליחה לליבה.
          </p>
        ) : null}

        {offline ? (
          <p className="rounded-lg bg-sky-50 px-4 py-3 text-sm text-sky-950 dark:bg-sky-950/40 dark:text-sky-100">
            אין חיבור לרשת - הדוח יסומן כ<strong>ממתין לשליחה</strong> ויועלה
            אוטומטית כשהרשת תחזור.
          </p>
        ) : (
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            לאחר אישור, הדוח יועבר לתור השליחה ויישלח לליבה.
          </p>
        )}

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

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
            disabled={loading || !hasLocalPdf}
            onClick={onConfirm}
          >
            {loading
              ? "שולח..."
              : offline
                ? "אשר - ממתין לרשת"
                : "אשר ושלח לליבה"}
          </Button>
        </div>
      </div>
    </div>
  );
}
