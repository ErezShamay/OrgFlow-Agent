/** תווית תצוגה לשדה ריק - לא נשמרת כערך בטופס או ב-API. */
export const UNSPECIFIED_FIELD_LABEL_HE = "לא צוין";

const UNSPECIFIED_FIELD_LABELS = new Set([
  UNSPECIFIED_FIELD_LABEL_HE,
  "לא מצוין",
]);

/** מנקה ערכי placeholder ישנים לפני הצגה בשדה עריכה. */
export function normalizeOptionalTextInput(value?: string | null): string {
  const trimmed = value?.trim() ?? "";
  if (!trimmed || UNSPECIFIED_FIELD_LABELS.has(trimmed)) {
    return "";
  }
  return trimmed;
}

/** תצוגת קריאה בלבד לשדה טקסט אופציונלי. */
export function displayOptionalText(value?: string | null): string {
  return normalizeOptionalTextInput(value) || UNSPECIFIED_FIELD_LABEL_HE;
}

/** ממיר ערך טופס לשמירה - placeholder לא נשמר. */
export function optionalTextForSave(value: string): string | null {
  const normalized = normalizeOptionalTextInput(value);
  return normalized || null;
}
