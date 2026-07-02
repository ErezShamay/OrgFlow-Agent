import type {
  FieldReportDocumentType,
  VisitScope,
} from "@/lib/field-reports/schema/types";

/** שלב 1 ב-wizard — §3.3 FIELD-REPORT-FINALIZE-PIPELINE. */
export const DOCUMENT_WIZARD_KINDS = [
  "WEEKLY_APARTMENT",
  "WEEKLY_MULTI_APARTMENT",
  "WEEKLY_WHOLE_BUILDING",
  "WEEKLY_PUBLIC_AREA",
  "HANDOVER_PROTOCOL",
] as const;

export type DocumentWizardKind = (typeof DOCUMENT_WIZARD_KINDS)[number];

/** Placeholder — תוכן פרוטוקול מסירה טרם אושר (docs/FIELD-REPORT-CHECKLISTS.md §4). */
export const HANDOVER_PROTOCOL_WIZARD_ENABLED = false;

export const DOCUMENT_WIZARD_LABELS: Record<DocumentWizardKind, string> = {
  WEEKLY_APARTMENT: "דירה",
  WEEKLY_MULTI_APARTMENT: "מספר דירות בביקור אחד",
  WEEKLY_WHOLE_BUILDING: "כלל הבניין",
  WEEKLY_PUBLIC_AREA: "שטחים ציבוריים",
  HANDOVER_PROTOCOL: "פרוטוקולי מסירה",
};

export const DOCUMENT_WIZARD_DESCRIPTIONS: Record<DocumentWizardKind, string> = {
  WEEKLY_APARTMENT: "דוח ביקור שבועי — צ'קליסט דירה לפי שלב בנייה",
  WEEKLY_MULTI_APARTMENT:
    "דוח אחד לכמה דירות — עם סיכום מספר הדירות שנבקרו בביקור",
  WEEKLY_WHOLE_BUILDING: "דוח ביקור לכלל הבניין — דירות ושטחים משותפים",
  WEEKLY_PUBLIC_AREA: "דוח ביקור שבועי — צ'קליסט לובי, חניון, מדרגות…",
  HANDOVER_PROTOCOL: "פרוטוקול מסירת דירה / שטחים — בקרוב",
};

export function documentWizardKindEnabled(kind: DocumentWizardKind): boolean {
  if (kind === "HANDOVER_PROTOCOL") {
    return HANDOVER_PROTOCOL_WIZARD_ENABLED;
  }

  return true;
}

export function visitScopeFromDocumentWizardKind(
  kind: DocumentWizardKind
): VisitScope | null {
  switch (kind) {
    case "WEEKLY_APARTMENT":
      return "APARTMENT";
    case "WEEKLY_MULTI_APARTMENT":
      return "MULTI_APARTMENT";
    case "WEEKLY_WHOLE_BUILDING":
      return "WHOLE_BUILDING";
    case "WEEKLY_PUBLIC_AREA":
      return "PUBLIC_AREA";
    default:
      return null;
  }
}

export function documentTypeFromWizardKind(
  kind: DocumentWizardKind
): FieldReportDocumentType {
  return kind === "HANDOVER_PROTOCOL" ? "handover_protocol" : "weekly_inspection";
}

export function isWeeklyDocumentWizardKind(
  kind: DocumentWizardKind | null
): kind is
  | "WEEKLY_APARTMENT"
  | "WEEKLY_MULTI_APARTMENT"
  | "WEEKLY_WHOLE_BUILDING"
  | "WEEKLY_PUBLIC_AREA" {
  return (
    kind === "WEEKLY_APARTMENT"
    || kind === "WEEKLY_MULTI_APARTMENT"
    || kind === "WEEKLY_WHOLE_BUILDING"
    || kind === "WEEKLY_PUBLIC_AREA"
  );
}
