/**
 * Gate — שלב G (field-supervision-checklist-spec §16.G).
 * PDF לצ'קליסט supervision — סקשן, סטטוסים, תמונות, סיכום.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { buildVisitReportDocDefinition } from "@/lib/field-reports/pdf/build-doc-definition";
import { createPdfPrinter } from "@/lib/field-reports/pdf/font-loader";
import { renderBlocks } from "@/lib/field-reports/pdf/render-blocks";
import {
  CHECKLIST_STATUS_PDF_COLORS,
  renderSupervisionChecklist,
  summarizeSupervisionChecklistItems,
} from "@/lib/field-reports/pdf/supervision-checklist-pdf-section";
import {
  addCustomSupervisionItem,
  hideSupervisionCatalogItem,
  updateSupervisionChecklistItem,
} from "@/lib/field-reports/schema/checklist-item-mutations";
import { CHECKLIST_ITEM_STATUS_LABELS } from "@/lib/field-reports/supervision-labels";
import type {
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
} from "@/lib/field-reports/schema/types";

const UI_ROOT = path.resolve(__dirname, "../../..");
const FONT_PATH = path.join(
  UI_ROOT,
  "public/fonts/NotoSansHebrew-Regular.ttf"
);

const MINIMAL_PNG_DATA_URL =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

function catalogSupervisionItem(
  id: string,
  issue_name_he: string,
  sort_order: number
): SupervisionChecklistItem {
  return {
    id,
    catalog_issue_id: `CAT-${id}`,
    issue_name_he,
    category_id: "flooring",
    category_name_he: "ריצוף",
    top_family: "FINISHING_WORKS",
    standard_ref: 'ת"י 4438',
    status: "OK",
    notes: null,
    photo_ids: [],
    sort_order,
  };
}

function sampleSupervisionBlock(): SupervisionChecklistBlock {
  return {
    id: "checklist-main",
    kind: "supervision_checklist",
    title_he: "ביקור דירה 12",
    construction_stage: "FINISHING",
    visit_scope: "APARTMENT",
    apartment_number: "12",
    items: [
      {
        id: "item-ok",
        catalog_issue_id: "FIN-FLOOR-01",
        issue_name_he: "ריצוף שטוח",
        category_id: "flooring",
        category_name_he: "ריצוף",
        top_family: "FINISHING_WORKS",
        standard_ref: 'ת"י 4438',
        status: "OK",
        notes: null,
        photo_ids: [],
        sort_order: 0,
      },
      {
        id: "item-defect",
        catalog_issue_id: "FIN-WALL-01",
        issue_name_he: "טיח אחיד",
        category_id: "plaster",
        category_name_he: "טיח",
        top_family: "FINISHING_WORKS",
        standard_ref: 'ת"י 1920',
        status: "DEFECT",
        notes: "סדק בפינה",
        photo_ids: ["primary"],
        sort_order: 1,
      },
      {
        id: "item-na",
        catalog_issue_id: "SYS-VENT-01",
        issue_name_he: "איוורור",
        category_id: "mechanical",
        category_name_he: "מיזוג",
        top_family: "MECHANICAL_ELECTRICAL_SYSTEMS",
        standard_ref: 'ת"י 5281',
        status: "NOT_APPLICABLE",
        notes: null,
        photo_ids: [],
        sort_order: 2,
      },
      {
        id: "item-unchecked",
        catalog_issue_id: "FIN-PAINT-01",
        issue_name_he: "צבע אחיד",
        category_id: "paint",
        category_name_he: "צבע",
        top_family: "FINISHING_WORKS",
        standard_ref: 'ת"י 1530',
        status: "UNCHECKED",
        notes: "לא נגיש",
        photo_ids: [],
        sort_order: 3,
      },
    ],
  };
}

function collectTexts(content: unknown): string[] {
  if (!content) {
    return [];
  }
  if (typeof content === "string") {
    return [content];
  }
  if (Array.isArray(content)) {
    return content.flatMap((item) => collectTexts(item));
  }
  if (typeof content === "object") {
    const node = content as Record<string, unknown>;
    const texts: string[] = [];
    if (typeof node.text === "string") {
      texts.push(node.text);
    }
    for (const key of ["stack", "columns", "content", "body", "table"]) {
      if (key in node) {
        texts.push(...collectTexts(node[key]));
      }
    }
    return texts;
  }
  return [];
}

describe("supervision checklist stage G gate (§16.G)", () => {
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

  it("supervision-checklist-pdf-section.ts exists and exports renderer", () => {
    const section = readSource(
      "lib/field-reports/pdf/supervision-checklist-pdf-section.ts"
    );
    const renderBlocksSource = readSource("lib/field-reports/pdf/render-blocks.ts");
    const resolveAssets = readSource("lib/field-reports/pdf/resolve-assets.ts");
    const generator = readSource(
      "lib/field-reports/pdf/generate-visit-report-pdf.ts"
    );

    expect(section).toContain("export function renderSupervisionChecklist");
    expect(section).toContain("groupSupervisionChecklistItems");
    expect(section).toContain("CHECKLIST_STATUS_PDF_COLORS");
    expect(renderBlocksSource).toContain(
      "...renderSupervisionChecklist(block, options)"
    );
    expect(resolveAssets).toContain("export async function resolveChecklistPhotos");
    expect(generator).toContain("resolveChecklistPhotos");
  });

  it("renderBlocks renders supervision_checklist (not empty stub)", () => {
    const block = sampleSupervisionBlock();
    const content = renderBlocks([block], {
      visitType: "FINISHING_APARTMENTS",
      projectName: "פרויקט שמש",
      visitDate: "2026-06-14",
      headerFields: {
        supervision_meta: {
          construction_stage: "FINISHING",
          visit_scope: "APARTMENT",
          apartment_number: "12",
        },
      },
      checklistPhotos: [
        {
          checklistItemId: "item-defect",
          dataUrl: MINIMAL_PNG_DATA_URL,
        },
      ],
    });

    const texts = collectTexts(content);
    expect(texts).toContain("ביקור דירה 12");
    expect(texts).toContain("גמר");
    expect(texts.some((text) => text.includes("דירה 12"))).toBe(true);
    expect(texts).toContain("ריצוף");
    expect(texts.some((text) => text.includes('ת"י 4438'))).toBe(true);
    expect(texts).toContain(CHECKLIST_ITEM_STATUS_LABELS.OK);
    expect(texts).toContain(CHECKLIST_ITEM_STATUS_LABELS.DEFECT);
    expect(texts).toContain(CHECKLIST_ITEM_STATUS_LABELS.NOT_APPLICABLE);
    expect(texts.some((text) => text.includes(CHECKLIST_ITEM_STATUS_LABELS.UNCHECKED))).toBe(
      true
    );
    expect(texts.some((text) => text.includes("ליקויים: 1"))).toBe(true);
    expect(texts.some((text) => text.includes("לא נבדק: 1"))).toBe(true);
  });

  it("maps all four statuses to Hebrew labels with PDF colors", () => {
    expect(CHECKLIST_STATUS_PDF_COLORS.OK).toBe("#16a34a");
    expect(CHECKLIST_STATUS_PDF_COLORS.DEFECT).toBe("#dc2626");
    expect(CHECKLIST_STATUS_PDF_COLORS.NOT_APPLICABLE).toBe("#6b7280");
    expect(CHECKLIST_STATUS_PDF_COLORS.UNCHECKED).toBe("#ea580c");

    const summary = summarizeSupervisionChecklistItems(sampleSupervisionBlock().items);
    expect(summary.defect_count).toBe(1);
    expect(summary.unchecked_count).toBe(1);
    expect(summary.unchecked_with_note_count).toBe(1);
    expect(summary.unchecked_without_note_count).toBe(0);
  });

  it("groups items by trade and category", () => {
    const content = renderSupervisionChecklist(sampleSupervisionBlock(), {
      projectName: "פרויקט",
      visitDate: "2026-06-14",
    });
    const texts = collectTexts(content);

    expect(texts).toContain("גמר");
    expect(texts).toContain("מערכות");
    expect(texts).toContain("ריצוף");
    expect(texts).toContain("טיח");
    expect(texts).toContain("מיזוג");
  });

  it("builds closed supervision report PDF with checklist section offline", async () => {
    const block = sampleSupervisionBlock();
    const doc = buildVisitReportDocDefinition({
      report: {
        id: "gate-supervision-pdf",
        visit_type: "FINISHING_APARTMENTS",
        visit_type_label_he: "גמר / דירות",
        visit_date: "2026-06-14",
        project_name: "פרויקט שמש",
        header_fields: {
          supervision_meta: {
            construction_stage: "FINISHING",
            visit_scope: "APARTMENT",
            apartment_number: "12",
          },
          blocks: [block],
        },
        lines: [],
      },
      checklistPhotos: [
        {
          checklistItemId: "item-defect",
          dataUrl: MINIMAL_PNG_DATA_URL,
        },
      ],
    });

    const texts = collectTexts(doc.content);
    expect(texts).toContain("סיכום צ'קליסט");
    expect(texts.some((text) => text.includes("ליקויים: 1"))).toBe(true);

    const pdfMake = await createPdfPrinter();
    const blob = await pdfMake.createPdf(doc).getBlob();
    expect(blob.size).toBeGreaterThan(2_000);
  }, 20_000);

  it("PRD §10 scenario 2 — omits hidden catalog items and includes custom item", () => {
    const catalogNames = [
      "ריצוף שטוח",
      "טיח אחיד",
      "איוורור",
      "צבע אחיד",
      "איטום קירות",
      "חשמל דירה",
    ];
    let items = catalogNames.map((name, index) =>
      catalogSupervisionItem(`cat-${index}`, name, index)
    );

    for (const item of items.slice(0, 5)) {
      items = hideSupervisionCatalogItem(items, item.id);
    }

    items = addCustomSupervisionItem(items);
    const customItem = items[items.length - 1];
    items = updateSupervisionChecklistItem(items, customItem.id, {
      issue_name_he: "בדיקת מערכת מיזוג ייעודית",
    });

    const block: SupervisionChecklistBlock = {
      ...sampleSupervisionBlock(),
      items,
    };

    const texts = collectTexts(
      renderSupervisionChecklist(block, {
        projectName: "פרויקט",
        visitDate: "2026-06-14",
      })
    );

    for (const hiddenName of catalogNames.slice(0, 5)) {
      expect(texts).not.toContain(hiddenName);
    }
    expect(texts).toContain("חשמל דירה");
    expect(texts).toContain("בדיקת מערכת מיזוג ייעודית");
  });
});
