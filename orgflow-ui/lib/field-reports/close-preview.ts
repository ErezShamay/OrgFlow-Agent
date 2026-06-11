export type ReportLineForClose = {
  id: string;
  description?: string | null;
  catalog_warning?: string | null;
};

export type ClosePreview = {
  line_count: number;
  empty_line_count: number;
  empty_line_ids: string[];
  catalog_warning_count: number;
  warnings: string[];
};

export function buildClosePreview(
  lines: ReportLineForClose[]
): ClosePreview {
  const emptyLines = lines.filter(
    (line) => !String(line.description || "").trim()
  );
  const catalogWarnings = lines.filter((line) =>
    Boolean(line.catalog_warning)
  );

  const warnings: string[] = [];

  if (!lines.length) {
    warnings.push("אין שורות ממצאים בדוח.");
  }

  if (emptyLines.length) {
    warnings.push(
      `${emptyLines.length} שורות ללא תיאור - מומלץ למלא לפני הפקת PDF.`
    );
  }

  if (catalogWarnings.length) {
    warnings.push(
      `${catalogWarnings.length} שורות עם אזהרת מפרט - מומלץ לבדוק לפני סגירה.`
    );
  }

  return {
    line_count: lines.length,
    empty_line_count: emptyLines.length,
    empty_line_ids: emptyLines.map((line) => line.id),
    catalog_warning_count: catalogWarnings.length,
    warnings,
  };
}
