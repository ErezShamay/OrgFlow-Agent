import { describe, expect, it } from "vitest";

import {
  migrateLegacyFinishingBlocks,
  shouldMigrateLegacyFinishingBlocks,
} from "@/lib/field-reports/schema/migrate-legacy-finishing-blocks";
import { normalizeReportBlocks } from "@/lib/field-reports/schema/normalize";
import { dualWriteHeaderBlocksAndProgress } from "@/lib/field-reports/schema/blocks-storage";

describe("migrateLegacyFinishingBlocks", () => {
  it("converts legacy progress + grouped lines to checklist and split findings", () => {
    const blocks = migrateLegacyFinishingBlocks(
      {
        construction_progress: [
          {
            description: "עבודות גמר בדירות הבעלים",
            status: "בוצע",
            completion_date: "01.04.25",
          },
          {
            description: "מערכות חשמל בדירות",
            status: "בתהליך",
            completion_date: "",
          },
          {
            description: "לובי / מעברים",
            status: "בוצע",
            completion_date: "15.03.25",
          },
        ],
      },
      [
        {
          id: "line-lobby",
          sort_order: 0,
          location: "לובי",
          trade: "ריצוף",
          status: "בוצע",
          description: "הושלם ריצוף",
          group_key: "floor:2",
          group_label_he: "קומה 2",
        },
        {
          id: "line-apt",
          sort_order: 1,
          location: "מטבח",
          trade: "אינסטלציה",
          status: "יש להשלים",
          description: "חיבור כיור",
          group_key: "apartment:3",
          group_label_he: "דירה 3",
        },
      ]
    );

    expect(blocks).toHaveLength(3);
    expect(blocks[0]).toMatchObject({
      kind: "checklist",
      title_he: "התקדמות הבנייה",
    });

    const checklist = blocks[0];
    if (checklist.kind !== "checklist") {
      throw new Error("expected checklist block");
    }

    const owners = checklist.items.find((item) => item.id === "checklist-owners");
    const electrical = checklist.items.find(
      (item) => item.id === "checklist-electrical"
    );
    expect(owners?.checked).toBe(true);
    expect(electrical?.checked).toBe(false);
    expect(electrical?.notes).toContain("בתהליך");

    const lobby = blocks.find((block) => block.id === "default-lobby-findings");
    const apartments = blocks.find(
      (block) => block.id === "default-apartment-findings"
    );

    expect(
      lobby?.kind === "findings_table" ? lobby.rows.length : 0
    ).toBeGreaterThanOrEqual(2);
    expect(
      apartments?.kind === "findings_table" ? apartments.rows : []
    ).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: "line-apt", block_id: "default-apartment-findings" }),
      ])
    );
  });

  it("is wired through normalizeReportBlocks for legacy finishing reports", () => {
    const blocks = normalizeReportBlocks(
      {
        construction_progress: [
          {
            description: "מערכות אינסטלציה בדירות",
            status: "בוצע",
            completion_date: "",
          },
        ],
      },
      "FINISHING_APARTMENTS",
      []
    );

    expect(blocks[0]?.kind).toBe("checklist");
    expect(blocks.some((block) => block.id === "default-lobby-findings")).toBe(
      true
    );
  });

  it("does not re-migrate modern finishing blocks", () => {
    const modern = normalizeReportBlocks(
      {
        blocks: [
          {
            id: "default-finishing-checklist",
            kind: "checklist",
            title_he: "התקדמות הבנייה",
            sort_order: 0,
            items: [
              {
                id: "checklist-owners",
                label_he: "בעלים",
                checked: true,
                sort_order: 0,
              },
            ],
          },
        ],
        construction_progress: [
          {
            description: "legacy row",
            status: "בוצע",
            completion_date: "",
          },
        ],
      },
      "FINISHING_APARTMENTS"
    );

    expect(modern).toHaveLength(1);
    expect(shouldMigrateLegacyFinishingBlocks("FINISHING_APARTMENTS", {}, modern)).toBe(
      false
    );
  });

  it("skips progress dual-write when finishing checklist blocks are present", () => {
    const blocks = normalizeReportBlocks(
      {
        blocks: [
          {
            id: "default-finishing-checklist",
            kind: "checklist",
            title_he: "התקדמות הבנייה",
            sort_order: 0,
            items: [],
          },
        ],
      },
      "FINISHING_APARTMENTS"
    );

    const synced = dualWriteHeaderBlocksAndProgress(
      blocks,
      [
        {
          description: "legacy progress",
          status: "בוצע",
          completion_date: "",
        },
      ],
      "FINISHING_APARTMENTS"
    );

    expect(synced.blocks).toHaveLength(1);
    expect(synced.blocks[0]?.kind).toBe("checklist");
  });
});
