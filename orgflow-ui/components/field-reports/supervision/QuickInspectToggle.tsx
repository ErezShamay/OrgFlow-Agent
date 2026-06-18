"use client";

import type { ChecklistItemStatus } from "@/lib/field-reports/schema/types";
import { FR_TOUCH_BUTTON } from "@/lib/field-reports/touch-input-class";

type QuickInspectToggleProps = {
  status: ChecklistItemStatus;
  disabled?: boolean;
  onStatusChange: (status: ChecklistItemStatus) => void;
};

export default function QuickInspectToggle({
  status,
  disabled = false,
  onStatusChange,
}: QuickInspectToggleProps) {

  function handleOkClick() {
    onStatusChange(status === "OK" ? "UNCHECKED" : "OK");
  }

  function handleDefectClick() {
    onStatusChange(status === "DEFECT" ? "UNCHECKED" : "DEFECT");
  }

  function handleNotApplicableClick() {
    onStatusChange(
      status === "NOT_APPLICABLE" ? "UNCHECKED" : "NOT_APPLICABLE"
    );
  }

  const okSelected = status === "OK";
  const defectSelected = status === "DEFECT";
  const notApplicableSelected = status === "NOT_APPLICABLE";

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        disabled={disabled}
        aria-label="תקין"
        aria-pressed={okSelected}
        className={`inline-flex min-h-12 min-w-12 items-center justify-center rounded-xl border text-lg font-bold transition-colors ${FR_TOUCH_BUTTON} ${
          okSelected
            ? "border-emerald-600 bg-emerald-600 text-white"
            : "border-zinc-200 bg-white text-emerald-700 dark:border-zinc-700 dark:bg-zinc-950 dark:text-emerald-400"
        }`}
        onClick={handleOkClick}
      >
        ✓
      </button>

      <button
        type="button"
        disabled={disabled}
        aria-label="ליקוי"
        aria-pressed={defectSelected}
        className={`inline-flex min-h-12 min-w-12 items-center justify-center rounded-xl border text-lg font-bold transition-colors ${FR_TOUCH_BUTTON} ${
          defectSelected
            ? "border-red-600 bg-red-600 text-white"
            : "border-zinc-200 bg-white text-red-700 dark:border-zinc-700 dark:bg-zinc-950 dark:text-red-400"
        }`}
        onClick={handleDefectClick}
      >
        ✗
      </button>

      <button
        type="button"
        disabled={disabled}
        aria-label="לא רלוונטי"
        aria-pressed={notApplicableSelected}
        title="לא רלוונטי (לחיצה ארוכה על הפריט)"
        className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${FR_TOUCH_BUTTON} ${
          notApplicableSelected
            ? "bg-zinc-600 text-white dark:bg-zinc-400 dark:text-zinc-900"
            : "border border-zinc-200 bg-white text-zinc-600 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300"
        }`}
        onClick={handleNotApplicableClick}
      >
        לא רלוונטי
      </button>
    </div>
  );
}
