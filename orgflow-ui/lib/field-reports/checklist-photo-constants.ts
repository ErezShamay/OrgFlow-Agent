/** מקסימום תמונות לפריט צ'קליסט מפקח (§7.1). */
export const MAX_CHECKLIST_ITEM_PHOTOS = 3;

export const CHECKLIST_PHOTO_SLOT_IDS = ["primary", "2", "3"] as const;

export type ChecklistPhotoSlotId =
  (typeof CHECKLIST_PHOTO_SLOT_IDS)[number];
