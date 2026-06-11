/**
 * בדיקות פריסה מול example_reports - מחרוזות מפתח מדוח ההגנה / אורנים.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { buildVisitReportDocDefinition } from "@/lib/field-reports/pdf/build-doc-definition";
import { createPdfPrinter } from "@/lib/field-reports/pdf/font-loader";
import {
  PDF_REPORT_TITLE_HE,
  PDF_SUPERVISION_BANNER_HE,
} from "@/lib/field-reports/pdf/render-header";
import { defaultReportBlocksForVisitType } from "@/lib/field-reports/schema/block-defaults";
import { buildFixedTextBlocksForNewReport } from "@/lib/field-reports/schema/fixed-text-inject";

const FONT_PATH = resolve(
  process.cwd(),
  "public/fonts/NotoSansHebrew-Regular.ttf"
);

const EXAMPLE_REPORTS_DIR = resolve(
  process.cwd(),
  "../example_reports"
);

describe("example_reports PDF layout parity", () => {
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

  it("generated finishing report contains Hagana-style cover strings", async () => {
    const doc = buildVisitReportDocDefinition({
      report: {
        id: "parity-hagana",
        visit_type: "FINISHING_APARTMENTS",
        visit_type_label_he: "גמר דירות",
        visit_date: "2025-04-21",
        project_name: "ההגנה 29 גבעתיים",
        header_fields: {
          scheme: "TAMA38_DEMOLITION_REBUILD",
          scheme_label_he: 'התחדשות עירונית - פרויקט הריסה ובניה תמ"א',
          project_start_date: "2024-01-01",
          project_end_date: "2027-06-30",
          project_grace_end_date: "2027-12-31",
          structure_documentation_date: "2025-04-21",
          housing_units_count: 29,
          illustration_caption_he:
            "הדמיית הפרויקט להמחשה בלבד",
          stakeholders: [
            {
              id: "dev",
              role: "developer",
              name: 'אוראקל יזמות נדל"ן בע"מ',
            },
            {
              id: "pm",
              role: "site_manager",
              name: "אילן רייסנר",
            },
            {
              id: "law",
              role: "lawyer_tenants",
              name: "עו״ד אורלי גיא ועו״ד אליקים דרנג",
            },
            {
              id: "arch",
              role: "architect",
              name: "כנען גיא",
            },
          ],
          main_suppliers: [
            {
              id: "s1",
              category_he: "דלתות פנים",
              vendor_name: "פנדור",
            },
          ],
          blocks: defaultReportBlocksForVisitType("FINISHING_APARTMENTS"),
          fixed_text_blocks: buildFixedTextBlocksForNewReport({
            visitDate: "2025-04-21",
          }),
          include_fixed_text_blocks: true,
        },
        lines: [],
      },
      inspector: { full_name: "מפקח בדיקה" },
      linePhotos: [],
    });

    const contentText = JSON.stringify(doc.content);
    expect(contentText).toContain(PDF_REPORT_TITLE_HE);
    expect(contentText).toContain("פרטים כללים:");
    expect(contentText).toContain("עדכונים לפרויקט:");
    expect(contentText).toContain("ספקים עיקריים לפרויקט:");
    expect(contentText).toContain("-פנדור.דלתות פנים");
    expect(contentText).toContain("תיעוד המבנה מיום 21.04.2025");
    expect(contentText).toContain("התקדמות הבנייה");
    expect(contentText).toContain("התקדמות עבודות הגמר לובי קומה");
    expect(contentText).toContain("ממצאים בדירות");
    expect(contentText).toContain("בעלים");
    expect(contentText).toContain("איטום מרפסות");
    expect(typeof doc.header).toBe("function");

    const pdfMake = await createPdfPrinter();
    const blob = await pdfMake.createPdf(doc).getBlob();
    expect(blob.size).toBeGreaterThan(8_000);
  }, 20_000);

  it("example_reports PDFs exist locally for manual parity review", () => {
    const hagana = resolve(
      EXAMPLE_REPORTS_DIR,
      "דוח מפקח דיירים - 2025-04-21 - ההגנה 29 גבעתיים.pdf"
    );
    const buffer = readFileSync(hagana);
    expect(buffer.subarray(0, 4).toString()).toBe("%PDF");
    expect(buffer.length).toBeGreaterThan(100_000);
  });
});
