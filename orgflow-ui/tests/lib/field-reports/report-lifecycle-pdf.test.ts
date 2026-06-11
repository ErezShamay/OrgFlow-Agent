/**
 * FR-5.2 - PDF bytes non-empty for new (blocks) and legacy report shapes.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { buildVisitReportDocDefinition } from "@/lib/field-reports/pdf/build-doc-definition";
import { createPdfPrinter } from "@/lib/field-reports/pdf/font-loader";
import { defaultReportBlocksForVisitType } from "@/lib/field-reports/schema/block-defaults";
import type { VisitReportPdfInput } from "@/lib/field-reports/pdf/types";

const FONT_PATH = resolve(
  process.cwd(),
  "public/fonts/NotoSansHebrew-Regular.ttf"
);

describe("report lifecycle PDF generation (FR-5.2)", () => {
  beforeAll(() => {
    const fontBytes = readFileSync(FONT_PATH);
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("NotoSansHebrew")) {
          return new Response(fontBytes, { status: 200 });
        }
        throw new Error(`unexpected fetch: ${url}`);
      })
    );
  });

  afterAll(() => {
    vi.unstubAllGlobals();
  });

  async function pdfBlobFromInput(
    input: VisitReportPdfInput
  ): Promise<Blob> {
    const pdfMake = await createPdfPrinter();
    const docDefinition = buildVisitReportDocDefinition({
      ...input,
      linePhotos: input.linePhotos ?? [],
    });
    const pdf = pdfMake.createPdf(docDefinition);
    return pdf.getBlob() as Promise<Blob>;
  }

  it(
    "produces non-empty PDF for explicit blocks + grouped line with photo",
    async () => {
    const blocks = defaultReportBlocksForVisitType("FINISHING_APARTMENTS").map(
      (block) =>
        block.kind === "progress_table"
          ? {
              ...block,
              rows: [
                {
                  id: "row-1",
                  description: "ריצוף",
                  status: "בוצע",
                  completion_date: "01.06.26",
                  sort_order: 0,
                },
              ],
            }
          : block
    );

    const blob = await pdfBlobFromInput({
      report: {
        id: "lifecycle-blocks",
        visit_type: "FINISHING_APARTMENTS",
        visit_type_label_he: "גמר דירות",
        visit_date: "2026-01-15",
        project_name: "פרויקט בדיקה",
        header_fields: {
          blocks,
          project_metadata: {
            scheme: "TAMA38_STRENGTHENING",
            scheme_label_he: 'התחדשות עירונית - פרויקט חיזוק תמ"א',
          },
          fixed_text_blocks: [],
          include_fixed_text_blocks: false,
        },
        lines: [
          {
            id: "line-1",
            sort_order: 0,
            description: "איטום",
            group_key: "apartment:3",
            group_label_he: "דירה 3",
            has_photo: true,
          },
        ],
      },
      inspector: { full_name: "מפקח בדיקה" },
      linePhotos: [
        {
          lineId: "line-1",
          dataUrl:
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        },
      ],
    });

    expect(blob.size).toBeGreaterThan(500);
    expect(blob.type).toMatch(/pdf/i);
    },
    15_000
  );

  it(
    "produces non-empty PDF for legacy construction_progress without blocks",
    async () => {
    const blob = await pdfBlobFromInput({
      report: {
        id: "lifecycle-legacy",
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד / אתר",
        visit_date: "2026-06-01",
        project_name: "פרויקט בדיקה",
        header_fields: {
          construction_progress: [
            {
              description: "הריסה",
              status: "בוצע",
              completion_date: "18.11.25",
            },
          ],
          developer_name: "יזם בדיקה",
        },
        lines: [
          {
            id: "line-legacy",
            sort_order: 0,
            description: "ממצא שלד",
            location: "קומה 2",
          },
        ],
      },
      inspector: { full_name: "מפקח בדיקה" },
      linePhotos: [],
    });

    expect(blob.size).toBeGreaterThan(500);
    expect(blob.type).toMatch(/pdf/i);
    },
    15_000
  );
});
