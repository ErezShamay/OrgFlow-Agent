/**
 * Presets עמודות טבלה לפי 4 וריאציות מדוחות הלקוח (FR-0.4).
 */

import type { BlockColumnDef, ColumnPresetKey, ColumnPresets } from "./types";

/** עשירה: מיקום · מלאכה · סטטוס/הערות · תיאור · תמונות */
const RICH_COLUMNS: readonly BlockColumnDef[] = [
  { id: "location", header_he: "מיקום" },
  { id: "trade", header_he: "מלאכה" },
  { id: "status", header_he: "סטטוס / הערות" },
  { id: "description", header_he: "תיאור" },
  { id: "photos", header_he: "תמונות" },
] as const;

/** גמר דירות: מיקום · מלאכה · הערות · סטטוס/תיאור · תמונות (דוח ההגנה). */
const FINISHING_COLUMNS: readonly BlockColumnDef[] = [
  { id: "location", header_he: "מיקום" },
  { id: "trade", header_he: "מלאכה" },
  { id: "notes", header_he: "הערות" },
  { id: "status", header_he: "סטטוס / תיאור" },
  { id: "photos", header_he: "תמונות" },
] as const;

/** פשוטה: תיאור · הערות/לטיפול · תמונות */
const SIMPLE_COLUMNS: readonly BlockColumnDef[] = [
  { id: "description", header_he: "תיאור" },
  { id: "notes", header_he: "הערות / לטיפול" },
  { id: "photos", header_he: "תמונות" },
] as const;

/** התקדמות: תיאור עבודה · סטטוס · תאריך ביצוע/סיום */
const PROGRESS_COLUMNS: readonly BlockColumnDef[] = [
  { id: "description", header_he: "תיאור עבודה" },
  { id: "status", header_he: "סטטוס" },
  { id: "completion_date", header_he: "תאריך ביצוע / סיום" },
] as const;

/** שלד: תיאור · סטטוס / תאריך סיום */
const STRUCTURE_COLUMNS: readonly BlockColumnDef[] = [
  { id: "description", header_he: "תיאור" },
  { id: "status", header_he: "סטטוס / תאריך סיום" },
] as const;

/** מפת presets עמודות - תואמת כותרות ב-PDF לדוגמה. */
export const COLUMN_PRESETS: ColumnPresets = {
  rich: RICH_COLUMNS,
  simple: SIMPLE_COLUMNS,
  finishing: FINISHING_COLUMNS,
  progress: PROGRESS_COLUMNS,
  structure: STRUCTURE_COLUMNS,
};

/** מחזיר הגדרות עמודות ל-preset נתון. */
export function getColumnPreset(key: ColumnPresetKey): readonly BlockColumnDef[] {
  return COLUMN_PRESETS[key];
}

/** מחזיר כותרות עברית בלבד ל-preset (לשימוש ב-PDF / UI). */
export function getColumnPresetHeaders(key: ColumnPresetKey): string[] {
  return COLUMN_PRESETS[key].map((column) => column.header_he);
}
