import type { Content, TDocumentDefinitions } from "pdfmake/interfaces";

import { normalizeSupervisionMeta } from "../schema/normalize";
import {
  constructionProgressTitleHe,
  type ConstructionProgressRow,
} from "../construction-progress";
import { DEFAULT_WINTER_RECOMMENDATIONS_HE } from "../pdf-block-defaults";
import {
  collectInlineRenderedPhotoLineIds,
  hasExplicitBlocksInHeader,
  renderExplicitBlocksFromHeader,
} from "./render-blocks";
import {
  renderFixedTextBlocksFromHeader,
  shouldRenderLegacyContractorNotes,
  shouldRenderLegacyWinterSection,
} from "./render-fixed-text";
import {
  formatHeaderContact,
  formatOrgAddress,
  renderVisitReportHeader,
  resolveStringList,
} from "./render-header";
import {
  PDF_PAGE_MARGINS,
  renderRepeatingPageHeader,
} from "./render-page-banner";
import {
  buildRtlTableBody,
  PDF_DEFAULT_STYLE,
  PDF_DOCUMENT_STYLES,
  PDF_HEBREW_FONT,
  pdfText,
} from "./pdf-styles";
import type {
  PdfReportLine,
  VisitReportPdfInput,
} from "./types";
import {
  PDF_ISSUE_MARKER_COLUMN_HEADER_HE,
  resolvePdfIssueMarkerForLine,
  type PdfLineIssueMarkerMap,
} from "./pdf-issue-markers";
import { formatCatalogStandardCell } from "./format-catalog-standard-cell";

export { formatHeaderContact, formatOrgAddress, resolveStringList };
export { formatCatalogStandardCell } from "./format-catalog-standard-cell";


const LINE_STATUS_LABELS: Record<string, string> = {
  IN_PROGRESS: "בתהליך",
  DONE: "בוצע",
  NEEDS_ACTION: "יש להשלים",
};

export function buildFindingsTableColumns(
  lines: PdfReportLine[],
  lineIssueMarkers?: PdfLineIssueMarkerMap
): string[] {
  const hasCatalogLines = lines.some(
    (line) => Boolean(line.issue_id || line.catalog_reference_id)
  );
  const columns = ["מיקום", "מלאכה", "סטטוס / הערות", "תיאור"];
  if (hasCatalogLines) {
    columns.push("תקן", "חומרה");
  }
  if (lineIssueMarkers && lineIssueMarkers.size > 0) {
    columns.push(PDF_ISSUE_MARKER_COLUMN_HEADER_HE);
  }
  return columns;
}

export function buildFindingsTableBody(
  lines: PdfReportLine[],
  columns: string[],
  lineIssueMarkers?: PdfLineIssueMarkerMap
): string[][] {
  const includeStandard = columns.includes("תקן");

  return [...lines]
    .sort(
      (left, right) =>
        (left.sort_order ?? 0) - (right.sort_order ?? 0)
    )
    .map((line) => {
      const statusNotes = [
        line.status ? formatLineStatus(line.status) : "",
        line.notes || "",
      ]
        .filter(Boolean)
        .join(" - ");

      const row = [
        line.location || "",
        line.trade || "",
        statusNotes,
        line.description || "",
      ];

      if (includeStandard) {
        row.push(formatCatalogStandardCell(line));
        row.push(line.issue_id ? line.severity || "" : "");
      }

      if (columns.includes(PDF_ISSUE_MARKER_COLUMN_HEADER_HE)) {
        row.push(resolvePdfIssueMarkerForLine(line.id, lineIssueMarkers));
      }

      return row;
    });
}

export function resolveWinterRecommendationsText(
  headerFields: Record<string, unknown>
): string {
  const value = headerFields.winter_recommendations;
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return DEFAULT_WINTER_RECOMMENDATIONS_HE;
}

export function resolveConstructionProgressRows(
  headerFields: Record<string, unknown>
): ConstructionProgressRow[] {
  const raw = headerFields.construction_progress;
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .map((item) => normalizeConstructionProgressRow(item))
    .filter(
      (row) =>
        row.description || row.status || row.completion_date
    );
}

export function buildConstructionProgressTableBody(
  rows: ConstructionProgressRow[]
): string[][] {
  return rows.map((row) => [
    row.description,
    row.status,
    row.completion_date,
  ]);
}

export function buildPdfFilename(report: VisitReportPdfInput["report"]): string {
  const project = sanitizeFilename(report.project_name || "דוח-ביקור");
  const date = report.visit_date || "ללא-תאריך";
  return `דוח-מפקח-${project}-${date}.pdf`;
}

export function buildVisitReportDocDefinition(
  input: VisitReportPdfInput
): TDocumentDefinitions {
  const {
    report,
    inspector,
    linePhotos = [],
    checklistPhotos = [],
    logoDataUrl,
    illustrationDataUrl,
    generatedAt = new Date(),
    lineIssueMarkers,
  } = input;
  const profile = report.organization_profile_snapshot;
  const headerFields = report.header_fields || {};
  const orgName = profile?.organization_name || "ארגון";
  const useExplicitBlocks = hasExplicitBlocksInHeader(headerFields);
  const inlinePhotoLineIds = useExplicitBlocks
    ? collectInlineRenderedPhotoLineIds(
        headerFields,
        report.visit_type,
        report.lines,
        linePhotos
      )
    : new Set<string>();
  const appendixLinePhotos = linePhotos.filter(
    (photo) => !inlinePhotoLineIds.has(photo.lineId)
  );
  const tableColumns = useExplicitBlocks
    ? []
    : buildFindingsTableColumns(report.lines, lineIssueMarkers);
  const tableBody = useExplicitBlocks
    ? []
    : buildFindingsTableBody(
        report.lines,
        tableColumns,
        lineIssueMarkers
      );
  const generatedLabel = generatedAt.toLocaleDateString("he-IL");
  const contractorNotes = resolveStringList(headerFields.contractor_notes);
  const winterRecommendations = resolveWinterRecommendationsText(
    headerFields
  );
  const inspectorTitle =
    stringField(headerFields.inspector_title)
    || inspector?.professional_title
    || "";
  const inspectorLicense =
    stringField(headerFields.inspector_license)
    || inspector?.license_number
    || "";

  const content: Content[] = [
    ...renderVisitReportHeader({
      report,
      profile,
      logoDataUrl,
      illustrationDataUrl,
    }),
  ];

  if (hasExplicitBlocksInHeader(headerFields)) {
    content.push({ text: "", pageBreak: "before" });
    content.push(
      ...renderExplicitBlocksFromHeader(headerFields, {
        visitType: report.visit_type,
        reportLines: report.lines,
        linePhotos,
        checklistPhotos,
        lineIssueMarkers,
        projectName: report.project_name,
        visitDate: report.visit_date,
        supervisionMeta: normalizeSupervisionMeta(headerFields),
        headerFields,
      })
    );
  } else {
    content.push({ text: "", pageBreak: "before" });
    appendLegacyReportBody(content, {
      headerFields,
      visitType: report.visit_type,
      tableColumns,
      tableBody,
    });
  }

  content.push(
    ...renderFixedTextBlocksFromHeader(headerFields, report.visit_date)
  );

  if (shouldRenderLegacyWinterSection(headerFields)) {
    content.push(
      pdfText("המלצות חורף / עונת גשמים", {
        style: "sectionTitle",
        margin: [0, 12, 0, 6],
      })
    );
    content.push(
      pdfText(winterRecommendations, { margin: [0, 0, 0, 12] })
    );
  }

  if (
    contractorNotes.length
    && shouldRenderLegacyContractorNotes(headerFields)
  ) {
    content.push(
      pdfText("הערות נוספות לקבלן", {
        style: "sectionTitle",
        margin: [0, 0, 0, 4],
      })
    );
    content.push({
      ol: contractorNotes.map((item) => pdfText(item) as Content),
      margin: [0, 0, 0, 12],
    });
  }

  for (const photo of appendixLinePhotos) {
    content.push(
      pdfText(`תמונה - שורה ${photo.lineId.slice(0, 8)}`, {
        style: "photoCaption",
        margin: [0, 8, 0, 4],
      })
    );
    content.push({
      image: photo.dataUrl,
      width: 220,
      alignment: "right",
      margin: [0, 0, 0, 8],
    });
  }

  content.push(
    pdfText("חתימה", {
      style: "sectionTitle",
      margin: [0, 16, 0, 6],
    })
  );
  const signatureLines = [
    inspector?.full_name || "מפקח",
    inspectorTitle,
    inspectorLicense
      ? `מספר רישוי: ${inspectorLicense}`
      : "",
    orgName,
  ].filter((line) => line && line !== "-");

  content.push({
    stack: signatureLines.map((line) => pdfText(line)),
    margin: [0, 0, 0, 12],
  });

  return {
    info: {
      title: buildPdfFilename(report),
    },
    pageMargins: PDF_PAGE_MARGINS,
    defaultStyle: PDF_DEFAULT_STYLE,
    styles: PDF_DOCUMENT_STYLES,
    header: renderRepeatingPageHeader({
      visitDate: report.visit_date,
      profile,
    }),
    footer: (currentPage: number, pageCount: number) => ({
      columns: [
        {
          text: `עמוד ${currentPage} מתוך ${pageCount}`,
          font: PDF_HEBREW_FONT,
          alignment: "left",
          direction: "rtl",
          fontSize: 8,
          margin: [40, 0, 0, 0],
        },
        {
          text: `${generatedLabel} · ${orgName}`,
          font: PDF_HEBREW_FONT,
          alignment: "right",
          direction: "rtl",
          fontSize: 8,
          margin: [0, 0, 40, 0],
        },
      ],
    }),
    content,
  };
}

function stringField(value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  const text = String(value).trim();
  return text || "-";
}

function formatLineStatus(status: string): string {
  return LINE_STATUS_LABELS[status] || status;
}

function normalizeConstructionProgressRow(
  value: unknown
): ConstructionProgressRow {
  if (!value || typeof value !== "object") {
    return { description: "", status: "", completion_date: "" };
  }

  const row = value as Record<string, unknown>;
  return {
    description: progressField(row.description),
    status: progressField(row.status),
    completion_date: progressField(row.completion_date),
  };
}

function progressField(value: unknown): string {
  if (typeof value === "string") {
    return value.trim();
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value).trim();
}

function sanitizeFilename(value: string): string {
  return value.replace(/[^\w\u0590-\u05FF.-]+/g, "-").replace(/-+/g, "-");
}

/** גוף דוח legacy - ללא header_fields.blocks מפורש (FR-2.3 backward compat). */
function appendLegacyReportBody(
  content: Content[],
  input: {
    headerFields: Record<string, unknown>;
    visitType: string;
    tableColumns: string[];
    tableBody: string[][];
  }
): void {
  const { headerFields, visitType, tableColumns, tableBody } = input;

  const progressRows = resolveConstructionProgressRows(headerFields);
  if (progressRows.length) {
    const progressTitle = constructionProgressTitleHe(visitType);
    content.push(
      pdfText(progressTitle, {
        style: "sectionTitle",
        margin: [0, 12, 0, 6],
      })
    );
    const progressHeaders = [
      "תיאור עבודה",
      "סטטוס",
      "תאריך ביצוע / סיום",
    ];
    content.push({
      table: {
        headerRows: 1,
        widths: ["*", "auto", "auto"].reverse(),
        body: buildRtlTableBody(
          progressHeaders,
          buildConstructionProgressTableBody(progressRows)
        ),
      },
      layout: "lightHorizontalLines",
      margin: [0, 0, 0, 12],
    });
  }

  content.push(
    pdfText("ממצאים / עבודות", {
      style: "sectionTitle",
      margin: [0, 12, 0, 6],
    })
  );

  if (tableBody.length) {
    content.push({
      table: {
        headerRows: 1,
        widths: tableColumns.map(() => "*").reverse(),
        body: buildRtlTableBody(tableColumns, tableBody),
      },
      layout: "lightHorizontalLines",
      margin: [0, 0, 0, 12],
    });
  } else {
    content.push(
      pdfText("אין שורות ממצאים בדוח.", { margin: [0, 0, 0, 12] })
    );
  }
}
