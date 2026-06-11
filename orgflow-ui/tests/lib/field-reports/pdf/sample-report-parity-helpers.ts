import type { TDocumentDefinitions } from "pdfmake/interfaces";

import { buildVisitReportDocDefinition } from "@/lib/field-reports/pdf/build-doc-definition";
import type { VisitReportPdfInput } from "@/lib/field-reports/pdf/types";
import { defaultReportBlocksForVisitType } from "@/lib/field-reports/schema/block-defaults";
import { buildFixedTextBlocksForNewReport } from "@/lib/field-reports/schema/fixed-text-inject";
import type {
  FindingsTableBlock,
  FixedTextBlock,
  ReportBlock,
} from "@/lib/field-reports/schema/types";

import {
  ORENIM_7_JAN_2026,
  ORENIM_SAMPLE_FINDING_ROWS,
  ORENIM_STAKEHOLDERS,
  ORENIM_WINTER_RECOMMENDATIONS_HE,
} from "./fixtures/sample-reports-parity";

/** מנרמל טקסט שחולץ מ-PDF להשוואת substring. */
export function normalizePdfExtractedText(text: string): string {
  return text
    .replace(/\\"/g, '"')
    .replace(/[\u201c\u201d\u05f4"]/g, "")
    .replace(/\u200f/g, "")
    .replace(/\s+/g, "")
    .trim();
}

/** בודק התאמה גם כש-PDF extraction מאחד רווחים/מסיר גרשיים. */
export function pdfExtractContainsPhrase(
  extracted: string,
  phrase: string
): boolean {
  const normalizedExtract = normalizePdfExtractedText(extracted);
  const normalizedPhrase = normalizePdfExtractedText(phrase);
  return normalizedExtract.includes(normalizedPhrase);
}

/** בודק שכל המחרוזות מופיעות ב-doc definition (content + header). */
export function assertDocContainsStrings(
  doc: TDocumentDefinitions,
  strings: readonly string[]
): void {
  const headerText =
    typeof doc.header === "function"
      ? JSON.stringify(doc.header({}, 1))
      : JSON.stringify(doc.header ?? {});
  const contentText = JSON.stringify(doc.content ?? []);
  const combined = normalizePdfExtractedText(`${headerText}\n${contentText}`);

  for (const expected of strings) {
    const normalizedExpected = normalizePdfExtractedText(expected);
    if (!combined.includes(normalizedExpected)) {
      throw new Error(`missing expected PDF string: ${expected}`);
    }
  }
}

function withOrenimFindingsRows(blocks: ReportBlock[]): ReportBlock[] {
  return blocks.map((block) => {
    if (block.kind !== "findings_table") {
      return block;
    }
    const findingsBlock = block as FindingsTableBlock;
    if (findingsBlock.title_he !== "ממצאים נוספים") {
      return block;
    }
    return {
      ...findingsBlock,
      rows: ORENIM_SAMPLE_FINDING_ROWS.map((row) => ({ ...row })),
    };
  });
}

function orenimFixedTextBlocks(): FixedTextBlock[] {
  const blocks = buildFixedTextBlocksForNewReport({
    visitDate: ORENIM_7_JAN_2026.visit_date,
  }).map((block) => ({ ...block }));

  return blocks.map((block) => {
    if (block.kind === "winter_recommendations") {
      return {
        ...block,
        enabled: true,
        body_he: ORENIM_WINTER_RECOMMENDATIONS_HE,
      };
    }
    return block;
  });
}

export function buildOrenimSampleReportPdfInput(): VisitReportPdfInput {
  const blocks = withOrenimFindingsRows(
    defaultReportBlocksForVisitType(ORENIM_7_JAN_2026.visit_type)
  );

  return {
    report: {
      id: "parity-orenim-7",
      visit_type: ORENIM_7_JAN_2026.visit_type,
      visit_type_label_he: ORENIM_7_JAN_2026.visit_type_label_he,
      visit_date: ORENIM_7_JAN_2026.visit_date,
      project_name: ORENIM_7_JAN_2026.project_name,
      header_fields: {
        scheme: ORENIM_7_JAN_2026.scheme,
        scheme_label_he: ORENIM_7_JAN_2026.scheme_label_he,
        addressee_label_he: ORENIM_7_JAN_2026.addressee_label_he,
        structure_documentation_date:
          ORENIM_7_JAN_2026.structure_documentation_date,
        illustration_caption_he: "הדמיית הפרויקט להמחשה בלבד",
        stakeholders: ORENIM_STAKEHOLDERS.map((entry) => ({ ...entry })),
        blocks,
        fixed_text_blocks: orenimFixedTextBlocks(),
        include_fixed_text_blocks: true,
        agreement_notes: ["להוראות ההסכם"],
        contractor_notes: ["1", "2"],
      },
      lines: [],
    },
    inspector: {
      full_name: ORENIM_7_JAN_2026.inspector_name,
      license_number: ORENIM_7_JAN_2026.inspector_license,
    },
    linePhotos: [],
  };
}

export function buildOrenimSampleDocDefinition(): TDocumentDefinitions {
  return buildVisitReportDocDefinition(buildOrenimSampleReportPdfInput());
}
