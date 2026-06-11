import type { TDocumentDefinitions } from "pdfmake/interfaces";

import { createPdfPrinter } from "@/lib/field-reports/pdf/font-loader";
import {
  PDF_DEFAULT_STYLE,
  PDF_DOCUMENT_STYLES,
  PDF_HEBREW_FONT,
  pdfText,
} from "@/lib/field-reports/pdf/pdf-styles";
import type { QualityPeriodicReportResponse } from "@/lib/quality-issues/types";

export const DEFAULT_PERIODIC_REPORT_DAYS = 30;

export function formatPeriodicReportPeriod(
  report: QualityPeriodicReportResponse
): string {
  const start = new Date(report.period_start).toLocaleDateString("he-IL");
  const end = new Date(report.period_end).toLocaleDateString("he-IL");
  return `${start} - ${end}`;
}

export function buildPeriodicReportCsvFilename(
  report: QualityPeriodicReportResponse
): string {
  const end = report.period_end.slice(0, 10);
  return `qc-periodic-report-${end}.csv`;
}

export function buildPeriodicReportPdfFilename(
  report: QualityPeriodicReportResponse
): string {
  const end = report.period_end.slice(0, 10);
  return `qc-periodic-report-${end}.pdf`;
}

export function buildPeriodicReportCsv(
  report: QualityPeriodicReportResponse
): string {
  const lines: string[] = [];
  const push = (cells: (string | number)[]) => {
    lines.push(
      cells
        .map((cell) => {
          const value = String(cell ?? "");
          return /[",\n\r]/.test(value)
            ? `"${value.replace(/"/g, '""')}"`
            : value;
        })
        .join(",")
    );
  };

  push(["דוח תקופתי - בקרת איכות"]);
  push(["תקופה", formatPeriodicReportPeriod(report)]);
  push(["סה״כ ליקויים", report.summary.total_issues]);
  push(["פתוחים", report.summary.open_total]);
  push(["קריטיים פתוחים", report.summary.open_critical]);
  push(["סגורים", report.summary.closed_total]);
  push(["חוזרים", report.summary.recurring_total]);
  lines.push("");

  push([
    "פרויקט",
    "קבלן",
    "סה״כ",
    "פתוחים",
    "קריטיים",
    "חוזרים",
  ]);
  for (const project of report.projects) {
    push([
      project.project_name || project.project_id,
      project.contractor_name || "",
      project.issue_total,
      project.open_total,
      project.open_critical,
      project.recurring_total,
    ]);
  }

  lines.push("");
  push([
    "כותרת",
    "פרויקט",
    "סטטוס",
    "חומרה",
    "מלאכה",
    "סעיף מפרט",
    "חזרות",
  ]);
  for (const issue of report.issues) {
    push([
      issue.title,
      issue.project_name || issue.project_id,
      issue.status,
      issue.severity,
      issue.trade || "",
      issue.standard_ref || "",
      issue.recurrence_count,
    ]);
  }

  return `\uFEFF${lines.join("\r\n")}\r\n`;
}

export function downloadTextFile(
  content: string,
  filename: string,
  mimeType: string
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export function buildPeriodicReportDocDefinition(
  report: QualityPeriodicReportResponse
): TDocumentDefinitions {
  const projectRows = report.projects.slice(0, 12).map((project) => [
    pdfText(project.project_name || project.project_id),
    pdfText(String(project.open_total)),
    pdfText(String(project.open_critical)),
    pdfText(String(project.recurring_total)),
  ]);

  const issueRows = report.issues.slice(0, 20).map((issue) => [
    pdfText(issue.title),
    pdfText(issue.project_name || issue.project_id),
    pdfText(issue.status),
    pdfText(issue.severity),
    pdfText(issue.standard_ref || "-"),
  ]);

  return {
    defaultStyle: PDF_DEFAULT_STYLE,
    styles: PDF_DOCUMENT_STYLES,
    pageMargins: [40, 48, 40, 48],
    content: [
      {
        text: pdfText("דוח תקופתי - בקרת איכות"),
        style: "header",
        alignment: "right",
      },
      {
        text: pdfText(`תקופה: ${formatPeriodicReportPeriod(report)}`),
        alignment: "right",
        margin: [0, 0, 0, 12],
      },
      {
        ul: [
          pdfText(`סה״כ ליקויים: ${report.summary.total_issues}`),
          pdfText(`פתוחים: ${report.summary.open_total}`),
          pdfText(`קריטיים פתוחים: ${report.summary.open_critical}`),
          pdfText(`סגורים: ${report.summary.closed_total}`),
          pdfText(`חוזרים: ${report.summary.recurring_total}`),
        ],
        alignment: "right",
        margin: [0, 0, 0, 16],
      },
      {
        text: pdfText("דירוג פרויקטים"),
        style: "subheader",
        alignment: "right",
        margin: [0, 0, 0, 8],
      },
      {
        table: {
          widths: ["*", 50, 50, 50],
          body: [
            [
              pdfText("פרויקט"),
              pdfText("פתוחים"),
              pdfText("קריטי"),
              pdfText("חוזר"),
            ],
            ...projectRows,
          ],
        },
        layout: "lightHorizontalLines",
        margin: [0, 0, 0, 16],
      },
      {
        text: pdfText("ליקויים בתקופה"),
        style: "subheader",
        alignment: "right",
        margin: [0, 0, 0, 8],
      },
      {
        table: {
          widths: ["*", "*", 60, 60, 70],
          body: [
            [
              pdfText("כותרת"),
              pdfText("פרויקט"),
              pdfText("סטטוס"),
              pdfText("חומרה"),
              pdfText("מפרט"),
            ],
            ...issueRows,
          ],
        },
        layout: "lightHorizontalLines",
      },
    ],
  };
}

export async function generatePeriodicReportPdf(
  report: QualityPeriodicReportResponse
): Promise<Blob> {
  const pdfMake = await createPdfPrinter();
  const docDefinition = buildPeriodicReportDocDefinition(report);

  return new Promise((resolve, reject) => {
    try {
      const pdf = pdfMake.createPdf({
        ...docDefinition,
        defaultStyle: {
          ...PDF_DEFAULT_STYLE,
          font: PDF_HEBREW_FONT,
        },
      });
      pdf.getBlob((blob: Blob) => resolve(blob));
    } catch (error) {
      reject(error);
    }
  });
}

export async function downloadPeriodicReportPdf(
  report: QualityPeriodicReportResponse
): Promise<void> {
  const blob = await generatePeriodicReportPdf(report);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = buildPeriodicReportPdfFilename(report);
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
