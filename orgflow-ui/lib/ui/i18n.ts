export type Locale = "he" | "en";

export type TranslationKey =
  | "common.loading"
  | "common.retry"
  | "common.empty"
  | "common.offline"
  | "common.error"
  | "common.page"
  | "common.of"
  | "common.sort"
  | "common.filter"
  | "common.previous"
  | "common.next"
  | "projects.title"
  | "projects.empty";

const translations: Record<
  Locale,
  Record<TranslationKey, string>
> = {
  he: {
    "common.loading": "טוען...",
    "common.retry": "נסה שוב",
    "common.empty": "אין נתונים להצגה",
    "common.offline": "אין חיבור לאינטרנט",
    "common.error": "אירעה שגיאה",
    "common.page": "עמוד",
    "common.of": "מתוך",
    "common.sort": "מיון",
    "common.filter": "סינון",
    "common.previous": "הקודם",
    "common.next": "הבא",
    "projects.title": "פרויקטים",
    "projects.empty": "אין פרויקטים",
  },
  en: {
    "common.loading": "Loading...",
    "common.retry": "Retry",
    "common.empty": "No data to display",
    "common.offline": "You are offline",
    "common.error": "Something went wrong",
    "common.page": "Page",
    "common.of": "of",
    "common.sort": "Sort",
    "common.filter": "Filter",
    "common.previous": "Previous",
    "common.next": "Next",
    "projects.title": "Projects",
    "projects.empty": "No projects",
  },
};

export function translate(
  locale: Locale,
  key: TranslationKey
): string {
  return translations[locale][key] ?? key;
}

export function getDocumentDirection(
  locale: Locale
): "rtl" | "ltr" {
  return locale === "he" ? "rtl" : "ltr";
}
