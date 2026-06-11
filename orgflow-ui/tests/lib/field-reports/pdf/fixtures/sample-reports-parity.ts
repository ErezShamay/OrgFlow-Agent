/**
 * מחרוזות מפתח שחולצו מ-sample_reports/2026-01-05 - האורנים 7 הוד השרון.pdf
 * (pypdf extract - PDF לא ב-git; fixture זה מאפשר parity ב-CI).
 */
import {
  PDF_REPORT_TITLE_HE,
  PDF_SUPERVISION_BANNER_HE,
} from "@/lib/field-reports/pdf/render-header";
import { DEFAULT_SAFETY_DISCLAIMER_HE } from "@/lib/field-reports/schema/block-defaults";
import { STRUCTURE_SITE_PROGRESS_TITLE_HE } from "@/lib/field-reports/construction-progress";
import { getColumnPresetHeaders } from "@/lib/field-reports/schema/column-presets";
import { projectSchemeLabelHe } from "@/lib/field-reports/project-scheme-labels";

export const SAMPLE_REPORTS_DIR_NAME = "sample_reports";

/** דוח לקוח: האורנים 7 הוד השרון - ביקור שלד 5.1.2026. */
export const ORENIM_7_JAN_2026 = {
  filename: "2026-01-05 - האורנים 7 הוד השרון.pdf",
  visit_date: "2026-01-05",
  project_name: "האורנים 7 הוד השרון",
  visit_type: "STRUCTURE_SITE" as const,
  visit_type_label_he: "שלד",
  scheme: "TAMA38_STRENGTHENING" as const,
  scheme_label_he: projectSchemeLabelHe("TAMA38_STRENGTHENING"),
  addressee_label_he: "בעלי הקרקע האורנים",
  structure_documentation_date: "2026-01-05",
  page_count: 7,
  min_pdf_bytes: 200_000,
  inspector_name: "מהנדסת אמי חי, מפקחת בנייה",
  inspector_license: "ק. אורון ניהול פרויקטים",
} as const;

/** כותרות ומבנה שמופיעים בכל דוחות sample_reports / example_reports (שלד). */
export const ORENIM_STRUCTURE_LAYOUT_STRINGS = [
  PDF_SUPERVISION_BANNER_HE,
  PDF_REPORT_TITLE_HE,
  ORENIM_7_JAN_2026.scheme_label_he,
  "פרטים כללים:",
  "עדכונים לפרויקט:",
  DEFAULT_SAFETY_DISCLAIMER_HE,
  "הדמיית הפרויקט להמחשה בלבד",
  "תיעוד המבנה מיום",
  STRUCTURE_SITE_PROGRESS_TITLE_HE,
  "ממצאים נוספים",
] as const;

/** כותרות עמודות כפי שמופיעות בדוח (חילוץ PDF מאחד רווחים). */
export const ORENIM_COLUMN_HEADER_SNIPPETS = {
  structure: ["תיאור", "סטטוס / תאריך סיום"],
  simple: ["תיאור", "הערות / לטיפול", "תמונות"],
} as const;

/** קטעי תוכן ממצאים מתוך דוח הלקוח - לאימות שה-generator מציג שורות דומות. */
export const ORENIM_SAMPLE_FINDING_SNIPPETS = [
  "מזגנים",
  "בהתאם להתקדמות העבודה",
  "טייח גמר",
  "מייאקים",
] as const;

/** סוף דוח - המלצות חורף + חתימה (מ-sample_reports). */
export const ORENIM_END_MATTER_SNIPPETS = [
  "להלן המלצות המפקח",
  "יתבצע ניקיון יסודי בחצר הציבורית",
  "הערות נוספות",
] as const;

/** stakeholders מתוך דוח הלקוח. */
export const ORENIM_STAKEHOLDERS = [
  { id: "dev", role: "developer" as const, name: "ניצנים" },
  { id: "pm", role: "project_manager" as const, name: "עמנואל" },
  {
    id: "law",
    role: "lawyer_tenants" as const,
    name: 'איתי פיינה',
  },
] as const;

/** שורות ממצאים לדוח parity - מבוסס על תוכן ה-PDF. */
export const ORENIM_SAMPLE_FINDING_ROWS = [
  {
    id: "finding-ac-1",
    description:
      "בהתאם להתקדמות העבודה יש לבצע העתקת מעבי המזגנים עי טכנאי מזגנים מוסמך למניעת נזקים ופגיעות.",
    trade: "מזגנים",
    location: "קומה 2",
    sort_order: 0,
  },
  {
    id: "finding-plaster-1",
    description:
      'מצורף תיעוד לביצוע טייח גמר בגר/גבס בשילוב רשת ע"פ דרישות התקן.',
    location: "קומה 7",
    sort_order: 1,
  },
  {
    id: "finding-plaster-2",
    description: "מבוצע שימוש במייאקים ו/או פינות טיח , כהכנה לעבודות הטיח המיישר",
    location: "קומה 8",
    sort_order: 2,
  },
] as const;

/** טקסט המלצות חורף מותאם - כמו בדוח הלקוח (ינואר). */
export const ORENIM_WINTER_RECOMMENDATIONS_HE = `להלן המלצות המפקח לקראת הערכות האתר לגשמים בפרט ולעונת החורף בכלל:
1. יתבצע ניקיון יסודי בחצר הציבורית בקומת הקרקע כולל פתיחת ניקוזים/צמ"גים.
2. יבוצעו חגורות הפרדה /איטום של אזורים מהם יכולים לחדור מים לחדר המדרגות/פיר המעלית
3. יתבצע ניקוז של הגג הקיים/החדש ע"י יצירת שיפועים ופתחי ניקוז
4. בזמן גשמים באחריות מנהל העבודה לוודא סגירה של פתח חדר מדרגות למניעת חדירות מי גשמים לגרם מדרגות
5. יתבצע אכסון של חומרי בניין וחפצים רלוונטיים מחשש לנפילות/פגיעות בעקבות רוחות, גשמים וסופות
6. יתבצע חיזוק של הגידור ההיקפי והפיגום באתר מחשש לנפילות/פגיעות בעקבות רוחות גשמים וסופות
7. באחריות הקבלן לדאוג לבטיחות הדיירים ועוברי האורח ולוודא כי האתר ערוך מכל הבחינות לקראת עונת החורף והגשמים הצפויים
8. נושאים נוספים ככל שרלוונטיים לאתר הספציפי ולהבטחת שלום הדיירים (הבעלים והשוכרים) יהיו באחריות מלאה של מנהל העבודה`;

export function expectedColumnHeadersForOrenim(): {
  structure: string[];
  simple: string[];
} {
  return {
    structure: [...getColumnPresetHeaders("structure")],
    simple: [...getColumnPresetHeaders("simple")],
  };
}
