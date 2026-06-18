"use client";

import BaseChecklistItemPhotoCapture from "@/components/field-reports/ChecklistItemPhotoCapture";
import { isDefectMissingClosePhoto } from "@/lib/field-reports/checklist-close-validation";
import type { ChecklistItemStatus } from "@/lib/field-reports/schema/types";

type SupervisionChecklistItemPhotoCaptureProps = {
  status: ChecklistItemStatus;
  reportId: string;
  checklistItemId: string;
  photoIds: string[];
  disabled?: boolean;
  onPhotoIdsChange: (photoIds: string[]) => void;
};

/**
 * תמונת ליקוי — אופציונלית בסימון (V2); חובה רק לפני סגירת דוח.
 */
export default function SupervisionChecklistItemPhotoCapture({
  status,
  reportId,
  checklistItemId,
  photoIds,
  disabled = false,
  onPhotoIdsChange,
}: SupervisionChecklistItemPhotoCaptureProps) {
  const needsPhotoAtClose = isDefectMissingClosePhoto({
    status,
    photo_ids: photoIds,
  });

  return (
    <div className="space-y-1">
      <BaseChecklistItemPhotoCapture
        reportId={reportId}
        checklistItemId={checklistItemId}
        photoIds={photoIds}
        disabled={disabled}
        onPhotoIdsChange={onPhotoIdsChange}
      />

      {needsPhotoAtClose ? (
        <p className="text-xs text-amber-800 dark:text-amber-200">
          תמונה נדרשת לפני סגירת הדוח — ניתן לסמן ליקוי בלי תמונה בשטח.
        </p>
      ) : null}
    </div>
  );
}
