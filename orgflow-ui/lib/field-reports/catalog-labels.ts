/** תוויות משפחת מפרט - מסונכרן עם `app/config/field_report_catalog_labels.py`. */
export const CATALOG_TOP_FAMILY_LABELS_HE: Record<string, string> = {
  STRUCTURAL_WORKS: "שלד",
  FINISHING_WORKS: "גמר",
  MECHANICAL_ELECTRICAL_SYSTEMS: "מערכות",
  SYSTEM_WATERPROOFING_AND_INSULATION: "איטום",
  CUSTOM: "פריטים מותאמים",
};

/** תוויות חומרה - ערכי המפרט באנגלית (`Critical`, `High`, …). */
export const CATALOG_SEVERITY_LABELS_HE: Record<string, string> = {
  critical: "קריטי",
  high: "גבוה",
  medium: "בינוני",
  low: "נמוך",
};

export function catalogFamilyLabelHe(
  topFamily: string,
  labelHe?: string | null
): string {
  return (
    CATALOG_TOP_FAMILY_LABELS_HE[topFamily] ||
    labelHe?.trim() ||
    topFamily
  );
}

export function catalogSeverityLabelHe(
  severity: string | null | undefined
): string {
  const raw = severity?.trim();
  if (!raw) {
    return "";
  }

  return CATALOG_SEVERITY_LABELS_HE[raw.toLowerCase()] ?? raw;
}
