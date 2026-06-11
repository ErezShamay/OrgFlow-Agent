/** תווית KPI עם בידוד LTR לקיצור AI - מונע היפוך סדר בתצוגת RTL. */
export const AI_REVIEWS_KPI_LABEL = "ביקורות \u2066AI\u2069";

/**
 * מתקן שורות מעורבות עברית/אנגלית/מספרים שנשברות ב-RTL
 * (למשל «ביקורות 0: AI» במקום «ביקורות AI: 0»).
 */
export function normalizeRtlOperationalSummary(text: string): string {
  return text
    .replace(/ביקורות\s+AI\s*:/gu, "ביקורות בינה מלאכותית:")
    .replace(/סיכום\s+AI\s/gu, "סיכום בינה מלאכותית ")
    .replace(/פעולות\s+AI\s*:/gu, "פעולות בינה מלאכותית:");
}
