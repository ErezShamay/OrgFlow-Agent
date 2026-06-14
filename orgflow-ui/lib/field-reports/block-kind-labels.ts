import type { ColumnPresetKey, ReportBlockKind } from "./schema/types";
import { COLUMN_PRESET_KEYS } from "./schema/types";

/** תווית עברית לסוג בלוק בגוף הדוח (FR-2.2). */
export const REPORT_BLOCK_KIND_LABELS: Record<ReportBlockKind, string> = {
  progress_table: "טבלת התקדמות",
  findings_table: "טבלת ממצאים",
  checklist: "צ'קליסט",
  supervision_checklist: "צ'קליסט מפקח",
  free_text: "טקסט חופשי",
  image: "תמונה / הדמיה",
};

/** אפשרויות הוספת סעיף - ללא כפילות מיותרת של אותו kind (אופציונלי). */
export const ADDABLE_BLOCK_KINDS: readonly ReportBlockKind[] = [
  "progress_table",
  "findings_table",
  "checklist",
  "free_text",
  "image",
] as const;

const COLUMN_PRESET_LABELS: Record<ColumnPresetKey, string> = {
  rich: "עשירה",
  simple: "פשוטה",
  finishing: "גמר דירות",
  progress: "התקדמות",
  structure: "שלד",
};

export function columnPresetLabelHe(key: ColumnPresetKey): string {
  return COLUMN_PRESET_LABELS[key];
}

export const COLUMN_PRESET_OPTIONS = COLUMN_PRESET_KEYS.map((key) => ({
  value: key,
  label: COLUMN_PRESET_LABELS[key],
}));
