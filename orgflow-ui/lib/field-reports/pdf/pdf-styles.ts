import type { Content, TDocumentDefinitions } from "pdfmake/interfaces";

import { sanitizePdfHebrewText } from "./sanitize-hebrew";

/** שם הגופן ב-pdfmake - חייב להתאים ל-font-loader. */
export const PDF_HEBREW_FONT = "NotoSansHebrew";

export const PDF_DEFAULT_STYLE = {
  font: PDF_HEBREW_FONT,
  fontSize: 10,
  alignment: "right" as const,
  direction: "rtl" as const,
  lineHeight: 1.25,
};

export const PDF_DOCUMENT_STYLES: NonNullable<
  TDocumentDefinitions["styles"]
> = {
  headerBar: {
    font: PDF_HEBREW_FONT,
    fontSize: 8,
    color: "#444444",
    alignment: "right",
    direction: "rtl",
  },
  supervisionBanner: {
    font: PDF_HEBREW_FONT,
    fontSize: 11,
    bold: true,
    alignment: "center",
    direction: "rtl",
  },
  reportTitle: {
    font: PDF_HEBREW_FONT,
    fontSize: 16,
    bold: true,
    alignment: "center",
    direction: "rtl",
  },
  subTitle: {
    font: PDF_HEBREW_FONT,
    fontSize: 12,
    alignment: "center",
    direction: "rtl",
  },
  sectionTitle: {
    font: PDF_HEBREW_FONT,
    fontSize: 12,
    bold: true,
    alignment: "right",
    direction: "rtl",
  },
  tableHeader: {
    font: PDF_HEBREW_FONT,
    fontSize: 10,
    bold: true,
    alignment: "right",
    direction: "rtl",
    fillColor: "#f4f4f5",
  },
  tableCell: {
    font: PDF_HEBREW_FONT,
    fontSize: 10,
    alignment: "right",
    direction: "rtl",
  },
  photoCaption: {
    font: PDF_HEBREW_FONT,
    fontSize: 9,
    color: "#555555",
    alignment: "right",
    direction: "rtl",
  },
};

/** תא טבלה - מחרוזת או אובייקט תוכן (תמונות). */
export type PdfTableCell = string | Content;

/**
 * הופך סדר עמודות - pdfmake מצייר עמודה 0 משמאל; בדוח עברי העמודה הראשונה מימין.
 */
export function mirrorTableRowsForRtl<T>(rows: T[][]): T[][] {
  return rows.map((row) => [...row].reverse());
}

export function pdfText(
  text: string,
  extra: Partial<Exclude<Content, string>> = {}
): Content {
  return {
    text: sanitizePdfHebrewText(text),
    font: PDF_HEBREW_FONT,
    alignment: "right",
    direction: "rtl",
    ...extra,
  };
}

export function pdfTableCell(
  text: string,
  options: { header?: boolean } = {}
): Content {
  return {
    text: sanitizePdfHebrewText(text),
    style: options.header ? "tableHeader" : "tableCell",
  };
}

export function pdfTableRowFromStrings(
  cells: string[],
  options: { header?: boolean } = {}
): Content[] {
  return cells.map((cell) => pdfTableCell(cell, options));
}

export function buildRtlTableBody(
  headers: string[],
  dataRows: string[][]
): Content[][] {
  const body: Content[][] = [
    pdfTableRowFromStrings(headers, { header: true }),
    ...dataRows.map((row) => pdfTableRowFromStrings(row)),
  ];
  return mirrorTableRowsForRtl(body);
}

export function buildRtlTableBodyFromCells(
  headers: string[],
  dataRows: PdfTableCell[][]
): PdfTableCell[][] {
  const headerRow = headers.map((header) => pdfTableCell(header, { header: true }));
  const body: PdfTableCell[][] = [
    headerRow,
    ...dataRows.map((row) =>
      row.map((cell) =>
        typeof cell === "string"
          ? (cell ? pdfTableCell(cell) : pdfTableCell(""))
          : cell
      )
    ),
  ];
  return mirrorTableRowsForRtl(body);
}
