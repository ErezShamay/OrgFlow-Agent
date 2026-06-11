import { describe, expect, it } from "vitest";

import {
  DEFAULT_BLOCKS_BY_VISIT_TYPE,
  DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE,
  DEFAULT_SAFETY_DISCLAIMER_HE,
  VISIT_TYPE_MIXED,
  defaultFixedTextBlocks,
  defaultReportBlocksForVisitType,
} from "@/lib/field-reports/schema/block-defaults";
import { COLUMN_PRESET_KEYS } from "@/lib/field-reports/schema/types";

describe("DEFAULT_BLOCKS_BY_VISIT_TYPE", () => {
  it("includes presets for structure, finishing, and mixed visit types", () => {
    expect(Object.keys(DEFAULT_BLOCKS_BY_VISIT_TYPE).sort()).toEqual([
      "FINISHING_APARTMENTS",
      VISIT_TYPE_MIXED,
      "STRUCTURE_SITE",
    ]);
  });

  it("uses structure column preset for STRUCTURE_SITE progress block", () => {
    const blocks = defaultReportBlocksForVisitType("STRUCTURE_SITE");
    const progress = blocks.find((block) => block.kind === "progress_table");

    expect(progress).toMatchObject({
      kind: "progress_table",
      column_preset: "structure",
      title_he: "סטטוס בניה-שלד",
    });
    expect(progress && "rows" in progress ? progress.rows.length : 0).toBeGreaterThan(
      0
    );
  });

  it("uses Hagana-style finishing blocks: checklist, lobby and apartment findings", () => {
    const blocks = defaultReportBlocksForVisitType("FINISHING_APARTMENTS");
    const checklist = blocks.find((block) => block.kind === "checklist");
    const findings = blocks.filter((block) => block.kind === "findings_table");

    expect(blocks.map((block) => block.kind)).toEqual([
      "checklist",
      "findings_table",
      "findings_table",
    ]);
    expect(checklist).toMatchObject({
      kind: "checklist",
      title_he: "התקדמות הבנייה",
    });
    expect(checklist && checklist.kind === "checklist" ? checklist.items.length : 0).toBe(
      6
    );
    expect(findings[0]).toMatchObject({
      title_he: "התקדמות עבודות הגמר לובי קומה",
      column_preset: "finishing",
      rows: [],
    });
    expect(findings[1]).toMatchObject({
      title_he: "ממצאים בדירות",
      column_preset: "finishing",
      rows: [],
    });
  });

  it("returns progress and findings blocks for MIXED", () => {
    const blocks = defaultReportBlocksForVisitType(VISIT_TYPE_MIXED);

    expect(blocks.map((block) => block.kind)).toEqual([
      "progress_table",
      "findings_table",
    ]);
  });

  it("references only known column preset keys", () => {
    const presets = new Set<string>(COLUMN_PRESET_KEYS);

    for (const templates of Object.values(DEFAULT_BLOCKS_BY_VISIT_TYPE)) {
      for (const template of templates) {
        if (template.column_preset) {
          expect(presets.has(template.column_preset)).toBe(true);
        }
      }
    }
  });
});

describe("defaultFixedTextBlocks", () => {
  it("includes non-conformance and safety disclaimers from example PDFs", () => {
    const blocks = defaultFixedTextBlocks();

    expect(blocks[0].body_he).toBe(DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE);
    expect(blocks[1].body_he).toBe(DEFAULT_SAFETY_DISCLAIMER_HE);
  });
});
