import { describe, expect, it } from "vitest";

import {
  addBlock,
  constructionProgressToProgressRows,
  dualWriteHeaderBlocksAndProgress,
  findProgressTableBlock,
  normalizeBlocksFromHeader,
  progressRowsToConstructionProgress,
  removeBlock,
  reorderBlocks,
  serializeBlocksForApi,
  updateBlock,
} from "@/lib/field-reports/schema/blocks-storage";
import {
  normalizeHeaderFields,
  serializeHeaderFieldsForApi,
} from "@/lib/field-reports/header-fields";

describe("normalizeBlocksFromHeader", () => {
  it("auto-creates progress block from construction_progress when blocks missing", () => {
    const blocks = normalizeBlocksFromHeader(
      {
        construction_progress: [
          {
            description: "דיפון",
            status: "בוצע",
            completion_date: "2026-01-01",
          },
        ],
      },
      "STRUCTURE_SITE"
    );

    const progress = findProgressTableBlock(blocks);
    expect(progress).not.toBeNull();
    expect(progress?.rows).toHaveLength(1);
    expect(progress?.rows[0]?.description).toBe("דיפון");
  });

  it("auto-creates findings block from report lines (read-only derive)", () => {
    const blocks = normalizeBlocksFromHeader(
      {},
      "STRUCTURE_SITE",
      {
        lines: [
          {
            id: "line-1",
            location: "קומה 2",
            trade: "טיח",
            description: "סדק",
          },
        ],
      }
    );

    expect(blocks.some((block) => block.kind === "findings_table")).toBe(true);
  });

  it("prefers explicit blocks[] over legacy construction_progress", () => {
    const blocks = normalizeBlocksFromHeader(
      {
        blocks: [
          {
            id: "custom-progress",
            kind: "progress_table",
            title_he: "התקדמות מותאמת",
            column_preset: "progress",
            rows: [
              {
                id: "r1",
                description: "שורה מותאמת",
                status: "",
                completion_date: "",
              },
            ],
          },
        ],
        construction_progress: [
          { description: "legacy row", status: "", completion_date: "" },
        ],
      },
      "STRUCTURE_SITE"
    );

    const progress = findProgressTableBlock(blocks);
    expect(progress?.id).toBe("custom-progress");
    expect(progress?.rows[0]?.description).toBe("שורה מותאמת");
  });
});

describe("blocks CRUD helpers", () => {
  it("adds, updates, removes and reorders blocks", () => {
    const initial = normalizeBlocksFromHeader({}, "STRUCTURE_SITE");
    const withFreeText = addBlock(initial, {
      id: "free-1",
      kind: "free_text",
      title_he: "הערות",
      body_he: "טקסט",
      sort_order: 99,
    });

    expect(withFreeText).toHaveLength(initial.length + 1);

    const updated = updateBlock(withFreeText, "free-1", (block) =>
      block.kind === "free_text"
        ? { ...block, body_he: "עודכן" }
        : block
    );
    const freeText = updated.find(
      (block) => block.id === "free-1" && block.kind === "free_text"
    );
    expect(freeText?.kind === "free_text" && freeText.body_he).toBe("עודכן");

    const removed = removeBlock(updated, "free-1");
    expect(removed.some((block) => block.id === "free-1")).toBe(false);

    if (removed.length >= 2) {
      const reordered = reorderBlocks(removed, 0, 1);
      expect(reordered[0]?.id).toBe(removed[1]?.id);
    }
  });
});

describe("dual-write construction_progress", () => {
  it("does not inject progress_table for supervision_checklist reports", () => {
    const supervisionBlock = {
      id: "checklist-main",
      kind: "supervision_checklist" as const,
      title_he: "ביקור",
      construction_stage: "FINISHING" as const,
      visit_scope: "APARTMENT" as const,
      items: [],
      sort_order: 0,
    };

    const { blocks } = dualWriteHeaderBlocksAndProgress(
      [supervisionBlock],
      [],
      "FINISHING_APARTMENTS"
    );

    expect(blocks).toHaveLength(1);
    expect(blocks[0]?.kind).toBe("supervision_checklist");
  });

  it("syncs progress block rows with construction_progress", () => {
    const rows = constructionProgressToProgressRows([
      { description: "ביסוס", status: "בתהליך", completion_date: "" },
    ]);
    const { blocks, construction_progress } = dualWriteHeaderBlocksAndProgress(
      [],
      [{ description: "ביסוס", status: "בתהליך", completion_date: "" }],
      "STRUCTURE_SITE"
    );

    const progressBlock = findProgressTableBlock(blocks);
    expect(progressBlock?.rows).toEqual(rows);
    expect(construction_progress[0]?.description).toBe("ביסוס");
    expect(progressRowsToConstructionProgress(rows)[0]?.status).toBe("בתהליך");
  });
});

describe("header-fields integration", () => {
  it("serializes blocks[] alongside construction_progress", () => {
    const fields = normalizeHeaderFields(
      {
        construction_progress: [
          { description: "עבודה", status: "בוצע", completion_date: "2026-02-01" },
        ],
      },
      "STRUCTURE_SITE"
    );

    const payload = serializeHeaderFieldsForApi(fields);

    expect(Array.isArray(payload.blocks)).toBe(true);
    expect((payload.blocks as unknown[]).length).toBeGreaterThan(0);
    expect(Array.isArray(payload.construction_progress)).toBe(true);
    expect(serializeBlocksForApi(fields.blocks)).toEqual(payload.blocks);
  });

  it("round-trips legacy header without blocks key", () => {
    const raw = {
      developer_name: "יזם",
      construction_progress: [],
    };
    const normalized = normalizeHeaderFields(raw, "STRUCTURE_SITE");
    const again = normalizeHeaderFields(
      serializeHeaderFieldsForApi(normalized),
      "STRUCTURE_SITE"
    );

    expect(again.developer_name).toBe("יזם");
    expect(again.blocks.length).toBeGreaterThanOrEqual(0);
  });
});
