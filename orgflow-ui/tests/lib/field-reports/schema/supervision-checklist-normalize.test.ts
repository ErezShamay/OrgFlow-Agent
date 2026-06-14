import { describe, expect, it } from "vitest";

import {
  normalizeReportBlocks,
  normalizeSupervisionMeta,
} from "@/lib/field-reports/schema/normalize";

describe("normalizeSupervisionChecklistBlock", () => {
  it("normalizes supervision_checklist blocks from header_fields", () => {
    const blocks = normalizeReportBlocks(
      {
        blocks: [
          {
            kind: "supervision_checklist",
            id: "checklist-main",
            title_he: "ביקור דירה 5",
            construction_stage: "FINISHING",
            visit_scope: "APARTMENT",
            apartment_number: "5",
            items: [
              {
                id: "checklist-SUP-FIN-004",
                catalog_issue_id: "SUP-FIN-004",
                issue_name_he: "פוגות",
                category_id: "TILING",
                category_name_he: "ריצוף",
                top_family: "FINISHING_WORKS",
                standard_ref: 'ת"י 1555',
                status: "DEFECT",
                photo_ids: ["primary"],
              },
            ],
          },
        ],
      },
      "FINISHING_APARTMENTS"
    );

    expect(blocks).toHaveLength(1);
    expect(blocks[0]).toMatchObject({
      kind: "supervision_checklist",
      construction_stage: "FINISHING",
      visit_scope: "APARTMENT",
      apartment_number: "5",
    });

    if (blocks[0]?.kind !== "supervision_checklist") {
      throw new Error("expected supervision_checklist block");
    }

    expect(blocks[0].items[0]).toMatchObject({
      catalog_issue_id: "SUP-FIN-004",
      status: "DEFECT",
      photo_ids: ["primary"],
      standard_ref: 'ת"י 1555',
    });
  });

  it("preserves legacy checklist blocks unchanged", () => {
    const blocks = normalizeReportBlocks(
      {
        blocks: [
          {
            kind: "checklist",
            id: "legacy-checklist",
            title_he: "התקדמות",
            items: [{ id: "c1", label_he: "חשמל", checked: true }],
          },
        ],
      },
      "FINISHING_APARTMENTS"
    );

    expect(blocks[0]).toMatchObject({
      kind: "checklist",
      items: [{ label_he: "חשמל", checked: true }],
    });
  });
});

describe("normalizeSupervisionMeta", () => {
  it("reads supervision_meta from header_fields", () => {
    const meta = normalizeSupervisionMeta({
      supervision_meta: {
        construction_stage: "STRUCTURE",
        visit_scope: "PUBLIC_AREA",
        public_area_id: "LOBBY",
        public_area_label_he: "לובי / כניסה",
      },
    });

    expect(meta).toEqual({
      construction_stage: "STRUCTURE",
      visit_scope: "PUBLIC_AREA",
      apartment_id: null,
      apartment_number: null,
      owner_name: null,
      ad_hoc_apartment: false,
      public_area_id: "LOBBY",
      public_area_label_he: "לובי / כניסה",
    });
  });
});
