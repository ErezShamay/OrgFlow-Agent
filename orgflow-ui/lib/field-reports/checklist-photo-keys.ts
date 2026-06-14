import {
  CHECKLIST_PHOTO_SLOT_IDS,
  type ChecklistPhotoSlotId,
} from "@/lib/field-reports/checklist-photo-constants";

export const PRIMARY_CHECKLIST_PHOTO_ID: ChecklistPhotoSlotId = "primary";

/** מפתח אחסון blob לתמונת צ'קליסט (§7.2). */
export function checklistPhotoStorageKey(
  reportId: string,
  checklistItemId: string,
  photoId: string = PRIMARY_CHECKLIST_PHOTO_ID
): string {
  return `${reportId}:checklist-item:${checklistItemId}:${photoId}`;
}

export function nextChecklistPhotoSlotId(
  existingPhotoIds: readonly string[]
): ChecklistPhotoSlotId | null {
  for (const slot of CHECKLIST_PHOTO_SLOT_IDS) {
    if (!existingPhotoIds.includes(slot)) {
      return slot;
    }
  }

  return null;
}
