import type {
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
} from "@/lib/field-reports/schema/types";

export type ChecklistCloseErrorCode =
  | "DEFECT_MISSING_PHOTO"
  | "UNCHECKED_MISSING_NOTE";

export type ChecklistCloseError = {
  item_id: string;
  item_name_he: string;
  code: ChecklistCloseErrorCode;
  message: string;
};

export type ChecklistCloseValidationResult =
  | { ok: true }
  | { ok: false; errors: ChecklistCloseError[] };

/** ליקוי ללא תמונה — חוסם רק בסגירה (V2), לא בסימון X. */
export function isDefectMissingClosePhoto(
  item: Pick<SupervisionChecklistItem, "status" | "photo_ids">
): boolean {
  return item.status === "DEFECT" && item.photo_ids.length === 0;
}

export function listDefectsMissingClosePhoto(
  block: SupervisionChecklistBlock
): SupervisionChecklistItem[] {
  return block.items.filter(isDefectMissingClosePhoto);
}

function defectMissingPhotoError(
  item: SupervisionChecklistItem
): ChecklistCloseError {
  return {
    item_id: item.id,
    item_name_he: item.issue_name_he,
    code: "DEFECT_MISSING_PHOTO",
    message: `ליקוי ב"${item.issue_name_he}" דורש לפחות תמונה אחת`,
  };
}

function uncheckedMissingNoteError(
  item: SupervisionChecklistItem
): ChecklistCloseError {
  return {
    item_id: item.id,
    item_name_he: item.issue_name_he,
    code: "UNCHECKED_MISSING_NOTE",
    message: `פריט "${item.issue_name_he}" לא נבדק — נדרשת הערה`,
  };
}

/** כללי §8.1 — ולידציה לפני «סיום דוח». */
export function validateChecklistForClose(
  block: SupervisionChecklistBlock
): ChecklistCloseValidationResult {
  const errors: ChecklistCloseError[] = [];

  for (const item of block.items) {
    if (isDefectMissingClosePhoto(item)) {
      errors.push(defectMissingPhotoError(item));
    }

    if (item.status === "UNCHECKED" && !item.notes?.trim()) {
      errors.push(uncheckedMissingNoteError(item));
    }
  }

  if (errors.length) {
    return { ok: false, errors };
  }

  return { ok: true };
}

export function checklistCloseErrorsToMessages(
  errors: ChecklistCloseError[]
): string[] {
  return errors.map((error) => error.message);
}
