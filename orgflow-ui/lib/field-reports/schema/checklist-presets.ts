/**
 * פריטי צ'קליסט גמר - לפי דוח ההגנה (FR-2.4).
 */

import type { ChecklistBlock, ChecklistItem } from "./types";

/** מזהה בלוק צ'קליסט ברירת מחדל ב-preset FINISHING_APARTMENTS. */
export const DEFAULT_FINISHING_CHECKLIST_BLOCK_ID = "default-finishing-checklist";

/** כותרת צ'קליסט בדוח גמר - תחת «התקדמות הבנייה» (דוח ההגנה). */
export const DEFAULT_FINISHING_CHECKLIST_TITLE_HE = "התקדמות הבנייה";

/** הגדרות פריטים קבועות - סדר כמו בדוחות הלקוח. */
export const FINISHING_CHECKLIST_ITEM_DEFS: readonly {
  id: string;
  label_he: string;
}[] = [
  { id: "owners", label_he: "בעלים" },
  { id: "spaces", label_he: "בדיקת חללים" },
  { id: "electrical", label_he: "חשמל" },
  { id: "plumbing", label_he: "אינסטלציה" },
  { id: "wet_rooms_sealing", label_he: "איטום חדרים רטובים" },
  { id: "balcony_sealing", label_he: "איטום מרפסות" },
] as const;

/** פריטי צ'קליסט גמר עם מזהים יציבים - לעריכה ו-PDF. */
export function defaultFinishingChecklistItems(): ChecklistItem[] {
  return FINISHING_CHECKLIST_ITEM_DEFS.map((def, index) => ({
    id: `checklist-${def.id}`,
    label_he: def.label_he,
    checked: false,
    notes: null,
    sort_order: index,
  }));
}

/** בלוק צ'קליסט גמר מלא - לתבנית FINISHING_APARTMENTS. */
export function defaultFinishingChecklistBlock(
  options?: { id?: string; title_he?: string; sort_order?: number }
): ChecklistBlock {
  return {
    id: options?.id ?? DEFAULT_FINISHING_CHECKLIST_BLOCK_ID,
    kind: "checklist",
    title_he: options?.title_he ?? DEFAULT_FINISHING_CHECKLIST_TITLE_HE,
    sort_order: options?.sort_order ?? 0,
    items: defaultFinishingChecklistItems(),
  };
}
