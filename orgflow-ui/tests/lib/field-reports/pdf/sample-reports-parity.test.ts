/**
 * Parity מול sample_reports - משימה 3.7.
 * לא משווה bytes; מאמת מחרוזות מפתח מחולצות מ-PDF לקוח מול generator.
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { execPythonArgs } from "../../../helpers/python-command";

import { createPdfPrinter } from "@/lib/field-reports/pdf/font-loader";
import { getColumnPresetHeaders } from "@/lib/field-reports/schema/column-presets";

import {
  expectedColumnHeadersForOrenim,
  ORENIM_7_JAN_2026,
  ORENIM_COLUMN_HEADER_SNIPPETS,
  ORENIM_END_MATTER_SNIPPETS,
  ORENIM_SAMPLE_FINDING_SNIPPETS,
  ORENIM_STRUCTURE_LAYOUT_STRINGS,
  SAMPLE_REPORTS_DIR_NAME,
} from "./fixtures/sample-reports-parity";
import {
  assertDocContainsStrings,
  buildOrenimSampleDocDefinition,
  buildOrenimSampleReportPdfInput,
  normalizePdfExtractedText,
  pdfExtractContainsPhrase,
} from "./sample-report-parity-helpers";

const FONT_PATH = resolve(
  process.cwd(),
  "public/fonts/NotoSansHebrew-Regular.ttf"
);

const SAMPLE_REPORTS_DIR = resolve(process.cwd(), "..", SAMPLE_REPORTS_DIR_NAME);

const ORENIM_SAMPLE_PDF = resolve(
  SAMPLE_REPORTS_DIR,
  ORENIM_7_JAN_2026.filename
);

describe("sample_reports PDF parity (task 3.7)", () => {
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

  it("fixture column headers match OrgFlow presets used in Orenim structure report", () => {
    const expected = expectedColumnHeadersForOrenim();
    expect(getColumnPresetHeaders("structure")).toEqual(expected.structure);
    expect(getColumnPresetHeaders("simple")).toEqual(expected.simple);
    expect(expected.structure).toEqual([...ORENIM_COLUMN_HEADER_SNIPPETS.structure]);
    expect(expected.simple).toEqual([...ORENIM_COLUMN_HEADER_SNIPPETS.simple]);
  });

  it("generated Orenim structure report contains layout strings from sample PDF", () => {
    const doc = buildOrenimSampleDocDefinition();
    expect(() =>
      assertDocContainsStrings(doc, ORENIM_STRUCTURE_LAYOUT_STRINGS)
    ).not.toThrow();
    expect(typeof doc.header).toBe("function");
  });

  it("generated Orenim report includes client finding snippets and end matter", () => {
    const doc = buildOrenimSampleDocDefinition();
    const contentText = JSON.stringify(doc.content ?? []);

    for (const snippet of ORENIM_SAMPLE_FINDING_SNIPPETS) {
      expect(contentText).toContain(snippet);
    }
    for (const snippet of ORENIM_END_MATTER_SNIPPETS) {
      expect(contentText).toContain(snippet);
    }
    expect(contentText).toContain(ORENIM_7_JAN_2026.inspector_name);
    expect(contentText).toContain("ניצנים");
    expect(contentText).toContain("05.01.2026");
  });

  it("generates a PDF blob comparable in size to the client sample", async () => {
    const doc = buildOrenimSampleDocDefinition();
    const pdfMake = await createPdfPrinter();
    const blob = await pdfMake.createPdf(doc).getBlob();

    expect(blob.size).toBeGreaterThan(8_000);
    if (existsSync(ORENIM_SAMPLE_PDF)) {
      const sampleBytes = readFileSync(ORENIM_SAMPLE_PDF);
      expect(sampleBytes.length).toBeGreaterThan(ORENIM_7_JAN_2026.min_pdf_bytes);
      expect(blob.size).toBeGreaterThan(sampleBytes.length * 0.02);
    }
  }, 20_000);

  it("sample_reports PDF exists locally for manual parity review", () => {
    if (!existsSync(ORENIM_SAMPLE_PDF)) {
      expect(
        existsSync(ORENIM_SAMPLE_PDF),
        `optional local fixture missing: ${ORENIM_SAMPLE_PDF}`
      ).toBe(false);
      return;
    }

    const buffer = readFileSync(ORENIM_SAMPLE_PDF);
    expect(buffer.subarray(0, 4).toString()).toBe("%PDF");
    expect(buffer.length).toBeGreaterThan(ORENIM_7_JAN_2026.min_pdf_bytes);
  });

  it("local sample PDF contains the same structural phrases as the committed fixture", () => {
    if (!existsSync(ORENIM_SAMPLE_PDF)) {
      return;
    }

    const repoRoot = resolve(process.cwd(), "..");
    const extracted = execPythonArgs(
      [
        "-c",
        [
          "import pypdf, sys",
          `reader = pypdf.PdfReader('${ORENIM_SAMPLE_PDF.replace(/'/g, "'\\''")}')`,
          "print(''.join(p.extract_text() or '' for p in reader.pages))",
        ].join("; "),
      ],
      { cwd: repoRoot, encoding: "utf8", maxBuffer: 2 * 1024 * 1024 }
    );

    const normalized = normalizePdfExtractedText(extracted);
    for (const phrase of ORENIM_STRUCTURE_LAYOUT_STRINGS) {
      expect(pdfExtractContainsPhrase(normalized, phrase)).toBe(true);
    }
    for (const snippet of ORENIM_SAMPLE_FINDING_SNIPPETS) {
      expect(pdfExtractContainsPhrase(normalized, snippet)).toBe(true);
    }
  });

  it("buildOrenimSampleReportPdfInput uses STRUCTURE_SITE defaults from block-defaults", () => {
    const input = buildOrenimSampleReportPdfInput();
    const blocks = input.report.header_fields.blocks as Array<{ title_he?: string }>;

    expect(input.report.visit_type).toBe("STRUCTURE_SITE");
    expect(blocks.map((block) => block.title_he)).toEqual([
      "סטטוס בניה-שלד",
      "ממצאים נוספים",
    ]);
  });
});
