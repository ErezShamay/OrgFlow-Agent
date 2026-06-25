import { describe, expect, it } from "vitest";

import { buildVisitReportDocDefinition } from "@/lib/field-reports/pdf/build-doc-definition";
import {
  buildLinePhotoLookup,
  collectInlineRenderedPhotoLineIds,
  findingsPresetIncludesPhotosColumn,
  findingsTableHeadersForPreset,
  hasExplicitBlocksInHeader,
  renderBlocks,
  renderChecklist,
  renderFindingsTable,
  renderProgressTable,
  segmentFindingsRowsByGroup,
} from "@/lib/field-reports/pdf/render-blocks";
import {
  addChecklistItem,
  createEmptyChecklistItem,
  removeChecklistItem,
  updateChecklistItem,
} from "@/lib/field-reports/schema/checklist-item-mutations";
import { defaultFinishingChecklistBlock } from "@/lib/field-reports/schema/checklist-presets";
import type {
  ChecklistBlock,
  FindingsTableBlock,
  ProgressTableBlock,
  ReportBlock,
} from "@/lib/field-reports/schema/types";

describe("hasExplicitBlocksInHeader", () => {
  it("is false when blocks missing or empty", () => {
    expect(hasExplicitBlocksInHeader({})).toBe(false);
    expect(hasExplicitBlocksInHeader({ blocks: [] })).toBe(false);
  });

  it("is true when blocks array has items", () => {
    expect(
      hasExplicitBlocksInHeader({
        blocks: [{ id: "b1", kind: "free_text", title_he: "טקסט", body_he: "x" }],
      })
    ).toBe(true);
  });
});

describe("findingsTableHeadersForPreset", () => {
  it("uses progress preset column headers without photos", () => {
    expect(findingsTableHeadersForPreset("progress")).toEqual([
      "תיאור עבודה",
      "סטטוס",
      "תאריך ביצוע / סיום",
    ]);
  });

  it("uses rich preset headers including photos column", () => {
    expect(findingsTableHeadersForPreset("rich")).toEqual([
      "מיקום",
      "מלאכה",
      "סטטוס / הערות",
      "תיאור",
      "תמונות",
    ]);
  });

  it("uses simple preset headers including photos column", () => {
    expect(findingsTableHeadersForPreset("simple")).toEqual([
      "תיאור",
      "הערות / לטיפול",
      "תמונות",
    ]);
  });
});

describe("findingsPresetIncludesPhotosColumn", () => {
  it("is true for rich and simple presets", () => {
    expect(findingsPresetIncludesPhotosColumn("rich")).toBe(true);
    expect(findingsPresetIncludesPhotosColumn("simple")).toBe(true);
  });

  it("is false for progress and structure presets", () => {
    expect(findingsPresetIncludesPhotosColumn("progress")).toBe(false);
    expect(findingsPresetIncludesPhotosColumn("structure")).toBe(false);
  });
});

describe("buildLinePhotoLookup", () => {
  it("maps line ids to all data urls", () => {
    const lookup = buildLinePhotoLookup([
      { lineId: "line-1", dataUrl: "data:image/png;base64,abc" },
      {
        lineId: "line-1",
        photoId: "p2",
        dataUrl: "data:image/png;base64,def",
      },
      { lineId: "line-2", dataUrl: "" },
    ]);
    expect(lookup.get("line-1")).toEqual([
      "data:image/png;base64,abc",
      "data:image/png;base64,def",
    ]);
    expect(lookup.has("line-2")).toBe(false);
  });
});

describe("renderProgressTable", () => {
  it("renders section title and preset headers", () => {
    const block: ProgressTableBlock = {
      id: "p1",
      kind: "progress_table",
      title_he: "התקדמות מותאמת",
      column_preset: "progress",
      rows: [
        {
          id: "r1",
          description: "דיפון",
          status: "בוצע",
          completion_date: "1.1.26",
        },
      ],
    };

    const texts = collectTexts(renderProgressTable(block));
    expect(texts).toContain("התקדמות מותאמת");
    expect(texts).toContain("תיאור עבודה");
    expect(texts).toContain("דיפון");
  });
});

describe("renderFindingsTable", () => {
  it("appends catalog columns for rich preset with issue rows", () => {
    const block: FindingsTableBlock = {
      id: "f1",
      kind: "findings_table",
      title_he: "ממצאים",
      column_preset: "rich",
      rows: [
        {
          id: "1",
          issue_id: "STR-1",
          standard_ref: 'ת"י 466',
          severity: "High",
          description: "סדק",
        },
      ],
    };

    const texts = collectTexts(renderFindingsTable(block));
    expect(texts).toContain("תקן");
    expect(texts).toContain('ת"י 466');
    expect(texts).toContain("High");
  });

  it("embeds inline photo thumbnails in the photos column", () => {
    const block: FindingsTableBlock = {
      id: "f1",
      kind: "findings_table",
      title_he: "ממצאים עם תמונה",
      column_preset: "simple",
      rows: [
        {
          id: "line-photo",
          description: "סדק",
          has_photo: true,
        },
      ],
    };

    const content = renderFindingsTable(block, [
      { lineId: "line-photo", dataUrl: "data:image/png;base64,thumb" },
    ]);
    const images = collectImages(content);

    expect(collectTexts(content)).toContain("תמונות");
    expect(images.length).toBeGreaterThanOrEqual(1);
    expect(images[0]).toMatchObject({
      width: 40,
      height: 40,
    });
  });

  it("renders catalog reference alongside standard ref", () => {
    const block: FindingsTableBlock = {
      id: "f-catalog",
      kind: "findings_table",
      title_he: "ממצאים",
      column_preset: "rich",
      rows: [
        {
          id: "1",
          issue_id: "STR-1",
          standard_ref: 'ת"י 949',
          catalog_reference_id: "IL-STD-949-WATER",
          severity: "HIGH",
          description: "רטיבות",
        },
      ],
    };

    const texts = collectTexts(renderFindingsTable(block));
    expect(texts).toContain('ת"י 949 (IL-STD-949-WATER)');
  });

  it("limits inline photo thumbnails to two per row", () => {
    const block: FindingsTableBlock = {
      id: "f-max-photos",
      kind: "findings_table",
      title_he: "ממצאים",
      column_preset: "simple",
      rows: [
        {
          id: "line-multi",
          description: "פגם",
          photo_ids: ["p1", "p2", "p3"],
        },
      ],
    };

    const content = renderFindingsTable(block, [
      { lineId: "line-multi", photoId: "p1", dataUrl: "data:image/png;base64,a" },
      { lineId: "line-multi", photoId: "p2", dataUrl: "data:image/png;base64,b" },
      { lineId: "line-multi", photoId: "p3", dataUrl: "data:image/png;base64,c" },
    ]);

    expect(collectImages(content)).toHaveLength(2);
  });

  it("renders multiple inline thumbnails for one row", () => {
    const block: FindingsTableBlock = {
      id: "f-multi",
      kind: "findings_table",
      title_he: "ממצאים",
      column_preset: "simple",
      rows: [
        {
          id: "line-multi",
          description: "פגם",
          photo_ids: ["p1", "p2"],
        },
      ],
    };

    const content = renderFindingsTable(block, [
      { lineId: "line-multi", photoId: "p1", dataUrl: "data:image/png;base64,a" },
      { lineId: "line-multi", photoId: "p2", dataUrl: "data:image/png;base64,b" },
    ]);

    expect(collectImages(content)).toHaveLength(2);
  });

  it("renders group sub-headers for apartment-style rows", () => {
    const block: FindingsTableBlock = {
      id: "f1",
      kind: "findings_table",
      title_he: "ממצאים לפי דירה",
      column_preset: "simple",
      rows: [
        {
          id: "1",
          description: "סדק",
          group_key: "apartment:3",
          group_label_he: "דירה 3",
          sort_order: 0,
        },
        {
          id: "2",
          description: "איטום",
          group_key: "apartment:3",
          group_label_he: "דירה 3",
          sort_order: 1,
        },
        {
          id: "3",
          description: "ללא קיבוץ",
          sort_order: 2,
        },
      ],
    };

    const texts = collectTexts(renderFindingsTable(block));
    expect(texts).toContain("ממצאים לפי דירה");
    expect(texts).toContain("דירה 3");
    expect(texts).toContain("סדק");
    expect(texts).toContain("ללא קיבוץ");
  });
});

describe("segmentFindingsRowsByGroup", () => {
  it("splits rows by group_key while preserving order", () => {
    const segments = segmentFindingsRowsByGroup([
      {
        id: "1",
        description: "a",
        group_key: "floor:1",
        group_label_he: "קומה 1",
      },
      {
        id: "2",
        description: "b",
        group_key: "floor:1",
        group_label_he: "קומה 1",
      },
      { id: "3", description: "c" },
      {
        id: "4",
        description: "d",
        group_key: "floor:2",
        group_label_he: "קומה 2",
      },
    ]);

    expect(segments).toEqual([
      {
        groupLabelHe: "קומה 1",
        rows: [
          expect.objectContaining({ id: "1" }),
          expect.objectContaining({ id: "2" }),
        ],
      },
      {
        groupLabelHe: null,
        rows: [expect.objectContaining({ id: "3" })],
      },
      {
        groupLabelHe: "קומה 2",
        rows: [expect.objectContaining({ id: "4" })],
      },
    ]);
  });
});

describe("renderChecklist", () => {
  it("renders checklist title, labels, and notes in table", () => {
    const block = defaultFinishingChecklistBlock();
    block.items = block.items.map((item, index) =>
      index === 0
        ? { ...item, checked: true, notes: "תקין" }
        : item
    );

    const texts = collectTexts(renderChecklist(block));
    expect(texts).toContain("התקדמות הבנייה");
    expect(texts).toContain("בעלים");
    expect(texts).toContain("בוצע - תקין");
    expect(texts).toContain("לא בוצע");
  });

  it("PRD §10 scenario 1 — renders 5 items after remove 2, add 1, and rename", () => {
    const base = defaultFinishingChecklistBlock();
    let items = base.items;

    for (const label of ["חשמל", "אינסטלציה"]) {
      const target = items.find((item) => item.label_he === label);
      expect(target).toBeDefined();
      items = removeChecklistItem(items, target!.id);
    }

    const owners = items.find((item) => item.label_he === "בעלים");
    expect(owners).toBeDefined();
    items = updateChecklistItem(items, owners!.id, {
      label_he: "בעלים + מפרט",
    });

    items = addChecklistItem(items, {
      ...createEmptyChecklistItem(items.length),
      label_he: "בדיקת מעליות",
    });

    expect(items).toHaveLength(5);

    const block: ChecklistBlock = { ...base, items };
    const texts = collectTexts(renderChecklist(block));
    const expectedLabels = [
      "בעלים + מפרט",
      "בדיקת חללים",
      "איטום חדרים רטובים",
      "איטום מרפסות",
      "בדיקת מעליות",
    ];

    for (const label of expectedLabels) {
      expect(texts).toContain(label);
    }
    expect(texts).not.toContain("חשמל");
    expect(texts).not.toContain("אינסטלציה");
    expect(
      expectedLabels.filter((label) => texts.includes(label))
    ).toHaveLength(5);
  });
});

describe("renderBlocks", () => {
  it("renders multiple blocks in sort_order", () => {
    const blocks: ReportBlock[] = [
      {
        id: "f1",
        kind: "findings_table",
        title_he: "ממצאים",
        column_preset: "simple",
        rows: [{ id: "1", description: "ממצא" }],
        sort_order: 1,
      },
      {
        id: "p1",
        kind: "progress_table",
        title_he: "התקדמות",
        column_preset: "progress",
        rows: [
          {
            id: "r1",
            description: "עבודה",
            status: "",
            completion_date: "",
          },
        ],
        sort_order: 0,
      },
    ];

    const texts = collectTexts(
      renderBlocks(blocks, { visitType: "STRUCTURE_SITE" })
    );
    const progressIndex = texts.indexOf("התקדמות");
    const findingsIndex = texts.indexOf("ממצאים");
    expect(progressIndex).toBeGreaterThan(-1);
    expect(findingsIndex).toBeGreaterThan(progressIndex);
  });
});

describe("collectInlineRenderedPhotoLineIds", () => {
  it("returns line ids rendered inline in findings tables", () => {
    const lineIds = collectInlineRenderedPhotoLineIds(
      {
        blocks: [
          {
            id: "f1",
            kind: "findings_table",
            title_he: "ממצאים",
            column_preset: "simple",
            rows: [
              { id: "line-1", description: "א", has_photo: true },
              { id: "line-2", description: "ב" },
            ],
          },
        ],
      },
      "FINISHING_APARTMENTS",
      [],
      [{ lineId: "line-1", dataUrl: "data:image/png;base64,x" }]
    );

    expect(lineIds).toEqual(new Set(["line-1"]));
  });
});

describe("buildVisitReportDocDefinition with explicit blocks", () => {
  it("omits appendix photos when rendered inline in findings table", () => {
    const definition = buildVisitReportDocDefinition({
      report: {
        id: "r1",
        visit_type: "FINISHING_APARTMENTS",
        visit_type_label_he: "גמר",
        visit_date: "2026-06-01",
        project_name: "בדיקה",
        header_fields: {
          blocks: [
            {
              id: "custom-findings",
              kind: "findings_table",
              title_he: "ממצאים",
              column_preset: "simple",
              sort_order: 0,
              rows: [
                {
                  id: "line-photo",
                  description: "תיקון",
                  has_photo: true,
                },
              ],
            },
          ],
        },
        lines: [],
      },
      linePhotos: [
        { lineId: "line-photo", dataUrl: "data:image/png;base64,inline" },
      ],
    });

    const texts = collectTexts(definition.content);
    expect(texts).not.toContain("תמונה - שורה line-pho");
    expect(collectImages(definition.content).length).toBeGreaterThan(0);
  });

  it("uses block titles instead of legacy section titles", () => {
    const definition = buildVisitReportDocDefinition({
      report: {
        id: "r1",
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד",
        visit_date: "2026-06-01",
        project_name: "בדיקה",
        header_fields: {
          blocks: [
            {
              id: "custom-progress",
              kind: "progress_table",
              title_he: "סטטוס מותאם",
              column_preset: "progress",
              sort_order: 0,
              rows: [
                {
                  id: "r1",
                  description: "שורה מותאמת",
                  status: "בוצע",
                  completion_date: "",
                },
              ],
            },
            {
              id: "custom-findings",
              kind: "findings_table",
              title_he: "רשימת עבודות",
              column_preset: "simple",
              sort_order: 1,
              rows: [
                {
                  id: "line-1",
                  description: "תיקון",
                  notes: "דחוף",
                },
              ],
            },
          ],
          construction_progress: [
            {
              description: "לא אמור להופיע",
              status: "",
              completion_date: "",
            },
          ],
        },
        lines: [
          {
            id: "legacy-line",
            description: "לא אמור להופיע",
          },
        ],
      },
    });

    const texts = collectTexts(definition.content);
    expect(texts).toContain("סטטוס מותאם");
    expect(texts).toContain("רשימת עבודות");
    expect(texts).toContain("שורה מותאמת");
    expect(texts).not.toContain("ממצאים / עבודות");
    expect(texts).not.toContain("לא אמור להופיע");
  });
});

describe("renderSupervisionChecklist via renderBlocks", () => {
  it("renders grouped supervision checklist with summary", () => {
    const content = renderBlocks(
      [
        {
          id: "sc1",
          kind: "supervision_checklist",
          title_he: "ביקור לובי",
          construction_stage: "MIXED",
          visit_scope: "PUBLIC_AREA",
          public_area_id: "LOBBY",
          items: [
            {
              id: "i1",
              catalog_issue_id: "PUB-01",
              issue_name_he: "ריצוף כניסה",
              category_id: "flooring",
              category_name_he: "ריצוף",
              top_family: "FINISHING_WORKS",
              standard_ref: 'ת"י 4438',
              status: "DEFECT",
              notes: "שבר",
              photo_ids: ["primary"],
              sort_order: 0,
            },
          ],
        },
      ],
      {
        visitType: "FINISHING_APARTMENTS",
        projectName: "מגדלי הים",
        visitDate: "2026-06-01",
        headerFields: {
          supervision_meta: {
            construction_stage: "MIXED",
            visit_scope: "PUBLIC_AREA",
            public_area_id: "LOBBY",
            public_area_label_he: "לובי / כניסה",
          },
        },
        checklistPhotos: [
          {
            checklistItemId: "i1",
            dataUrl: "data:image/png;base64,thumb",
          },
        ],
      }
    );

    const texts = collectTexts(content);
    expect(texts).toContain("ביקור לובי");
    expect(texts.some((text) => text.includes("לובי / כניסה"))).toBe(true);
    expect(texts).toContain("ליקוי");
    expect(texts.some((text) => text.includes('ת"י 4438'))).toBe(true);
    expect(texts.some((text) => text.includes("ליקויים: 1"))).toBe(true);

    const images = collectImages(content);
    expect(images.some((image) => image.width === 40)).toBe(true);
  });

  it("does not affect legacy checklist block rendering", () => {
    const legacy = renderChecklist(defaultFinishingChecklistBlock());
    const texts = collectTexts(legacy);
    expect(texts.length).toBeGreaterThan(0);
  });
});

function collectImages(content: unknown): { width?: number; height?: number }[] {
  if (!content) {
    return [];
  }
  if (Array.isArray(content)) {
    return content.flatMap((item) => collectImages(item));
  }
  if (typeof content === "object") {
    const node = content as Record<string, unknown>;
    const images: { width?: number; height?: number }[] = [];
    if (typeof node.image === "string") {
      images.push({
        width: typeof node.width === "number" ? node.width : undefined,
        height: typeof node.height === "number" ? node.height : undefined,
      });
    }
    for (const key of ["stack", "columns", "content"]) {
      if (key in node) {
        images.push(...collectImages(node[key]));
      }
    }
    if ("table" in node && node.table && typeof node.table === "object") {
      const table = node.table as { body?: unknown };
      images.push(...collectImages(table.body));
    }
    return images;
  }
  return [];
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
    for (const key of ["stack", "ul", "ol", "columns", "content"]) {
      if (key in node) {
        texts.push(...collectTexts(node[key]));
      }
    }
    if ("table" in node && node.table && typeof node.table === "object") {
      const table = node.table as { body?: unknown };
      texts.push(...collectTexts(table.body));
    }
    return texts;
  }
  return [];
}
