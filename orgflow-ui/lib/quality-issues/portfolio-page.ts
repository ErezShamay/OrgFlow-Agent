/** Portfolio `/portfolio` page copy and layout helpers - roadmap 4.1.6. */

export const PORTFOLIO_QC_PAGE_EYEBROW = "תיק QC";

export const PORTFOLIO_QC_PAGE_TITLE = "תיק בקרת איכות";

export const PORTFOLIO_QC_PAGE_SUBTITLE =
  "תמונת מצב לפי ליקויים פתוחים, סגירה ודירוג פרויקטים - לא Health Score";

export const PORTFOLIO_LEGACY_SECTION_TITLE =
  "סקירה תפעולית";

export const PORTFOLIO_LEGACY_SECTION_SUMMARY =
  "Health Score, פעולות, הסלמות וביקורות AI";

export const PORTFOLIO_LEGACY_SECTION_HINT =
  "מוצג לצורך תאימות PM - דירוג QC למעלה הוא המקור העיקרי";

export const PORTFOLIO_LEGACY_RANKING_TITLE =
  "דירוג Health Score";

/** Legacy PM section starts collapsed so QC remains the primary view. */
export const PORTFOLIO_LEGACY_DEFAULT_EXPANDED = false;

export function portfolioLegacySectionId(): string {
  return "portfolio-legacy-section";
}
