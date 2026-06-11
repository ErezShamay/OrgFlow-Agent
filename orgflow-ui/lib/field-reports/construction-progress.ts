/** Construction-progress table (task 3C.6) - mirrors app/config/field_report_construction_progress.py */

export type ConstructionProgressRow = {
  description: string;
  status: string;
  completion_date: string;
};

export const STRUCTURE_SITE_PROGRESS_TITLE_HE = "סטטוס בניה-שלד";
export const FINISHING_APARTMENTS_PROGRESS_TITLE_HE = "התקדמות הבנייה";

/** טבלת ממצאים לאזורים משותפים - לובי / קומה (דוח גמר דירות). */
export const FINISHING_LOBBY_FINDINGS_TITLE_HE =
  "התקדמות עבודות הגמר לובי קומה";

/** טבלת ממצאים לדירות - מקובצת לפי «דירה N» ב-PDF. */
export const FINISHING_APARTMENT_FINDINGS_TITLE_HE = "ממצאים בדירות";

export const PROGRESS_STATUS_SUGGESTIONS = [
  "בוצע",
  "בתהליך",
  "סיום ביצוע",
  "לא בוצע",
  "חלקית",
] as const;

export const DEFAULT_STRUCTURE_SITE_PROGRESS_ROWS: ConstructionProgressRow[] =
  [
    { description: "הריסת המבנה", status: "", completion_date: "" },
    { description: "עבודות דיפון", status: "", completion_date: "" },
    { description: "חפירה חניון תת קרקעי", status: "", completion_date: "" },
    { description: "ביסוס המבנה", status: "", completion_date: "" },
    {
      description: "יציקת רצפה קומת מינוס 2",
      status: "",
      completion_date: "",
    },
    {
      description: "יציקת קירות קומת מינוס 2",
      status: "",
      completion_date: "",
    },
    {
      description: "יציקת רצפה קומת מינוס 1",
      status: "",
      completion_date: "",
    },
    {
      description: "יציקת קירות קומת מינוס 1",
      status: "",
      completion_date: "",
    },
    {
      description: "יציקת רצפת קומת קרקע",
      status: "",
      completion_date: "",
    },
  ];

export const DEFAULT_FINISHING_APARTMENTS_PROGRESS_ROWS: ConstructionProgressRow[] =
  [
    {
      description: "עבודות גמר בדירות הבעלים",
      status: "",
      completion_date: "",
    },
    { description: "חדר מדרגות", status: "", completion_date: "" },
    { description: "לובי / מעברים", status: "", completion_date: "" },
    {
      description: "מערכות חשמל בדירות",
      status: "",
      completion_date: "",
    },
    {
      description: "מערכות אינסטלציה בדירות",
      status: "",
      completion_date: "",
    },
    {
      description: "איטום חדרים רטובים ומרפסות",
      status: "",
      completion_date: "",
    },
  ];

const VISIT_TYPE_DEFAULTS: Record<string, ConstructionProgressRow[]> = {
  STRUCTURE_SITE: DEFAULT_STRUCTURE_SITE_PROGRESS_ROWS,
  FINISHING_APARTMENTS: DEFAULT_FINISHING_APARTMENTS_PROGRESS_ROWS,
  MIXED: DEFAULT_FINISHING_APARTMENTS_PROGRESS_ROWS,
};

const VISIT_TYPE_TITLES: Record<string, string> = {
  STRUCTURE_SITE: STRUCTURE_SITE_PROGRESS_TITLE_HE,
  FINISHING_APARTMENTS: FINISHING_APARTMENTS_PROGRESS_TITLE_HE,
  MIXED: FINISHING_APARTMENTS_PROGRESS_TITLE_HE,
};

export function constructionProgressTitleHe(visitType: string): string {
  return VISIT_TYPE_TITLES[visitType] || "התקדמות הבנייה";
}

export function defaultConstructionProgressRows(
  visitType: string
): ConstructionProgressRow[] {
  const rows = VISIT_TYPE_DEFAULTS[visitType];
  if (!rows) {
    return [];
  }
  return rows.map((row) => ({ ...row }));
}

export function normalizeConstructionProgressRows(
  value: unknown,
  visitType: string
): ConstructionProgressRow[] {
  if (!Array.isArray(value) || value.length === 0) {
    return defaultConstructionProgressRows(visitType);
  }

  return value.map((item) => normalizeConstructionProgressRow(item));
}

export function serializeConstructionProgressRows(
  rows: ConstructionProgressRow[]
): ConstructionProgressRow[] {
  return rows
    .map((row) => ({
      description: row.description.trim(),
      status: row.status.trim(),
      completion_date: row.completion_date.trim(),
    }))
    .filter(
      (row) =>
        row.description || row.status || row.completion_date
    );
}

function normalizeConstructionProgressRow(
  value: unknown
): ConstructionProgressRow {
  if (!value || typeof value !== "object") {
    return { description: "", status: "", completion_date: "" };
  }

  const row = value as Record<string, unknown>;
  return {
    description: stringField(row.description),
    status: stringField(row.status),
    completion_date: stringField(row.completion_date),
  };
}

function stringField(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}
