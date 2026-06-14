import { describe, expect, it } from "vitest";

import {
  validateChecklistForClose,
} from "@/lib/field-reports/checklist-close-validation";
import type { SupervisionChecklistBlock } from "@/lib/field-reports/schema/types";

function sampleBlock(
  items: SupervisionChecklistBlock["items"]
): SupervisionChecklistBlock {
  return {
    id: "checklist-main",
    kind: "supervision_checklist",
    title_he: "ביקור דירה 5",
    construction_stage: "FINISHING",
    visit_scope: "APARTMENT",
    apartment_number: "5",
    items,
  };
}

describe("validateChecklistForClose (§8.1)", () => {
  it("blocks DEFECT without photo", () => {
    const result = validateChecklistForClose(
      sampleBlock([
        {
          id: "checklist-SUP-FIN-004",
          catalog_issue_id: "SUP-FIN-004",
          issue_name_he: "פוגות",
          category_id: "TILING",
          category_name_he: "ריצוף",
          top_family: "FINISHING_WORKS",
          standard_ref: 'ת"י 1555',
          status: "DEFECT",
          photo_ids: [],
          sort_order: 0,
        },
      ])
    );

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.errors[0]?.code).toBe("DEFECT_MISSING_PHOTO");
      expect(result.errors[0]?.message).toContain("פוגות");
    }
  });

  it("blocks UNCHECKED without note", () => {
    const result = validateChecklistForClose(
      sampleBlock([
        {
          id: "checklist-SUP-FIN-004",
          catalog_issue_id: "SUP-FIN-004",
          issue_name_he: "פוגות",
          category_id: "TILING",
          category_name_he: "ריצוף",
          top_family: "FINISHING_WORKS",
          standard_ref: 'ת"י 1555',
          status: "UNCHECKED",
          notes: null,
          photo_ids: [],
          sort_order: 0,
        },
      ])
    );

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.errors[0]?.code).toBe("UNCHECKED_MISSING_NOTE");
    }
  });

  it("allows UNCHECKED with note and OK without photo", () => {
    const result = validateChecklistForClose(
      sampleBlock([
        {
          id: "checklist-1",
          catalog_issue_id: "SUP-FIN-004",
          issue_name_he: "פוגות",
          category_id: "TILING",
          category_name_he: "ריצוף",
          top_family: "FINISHING_WORKS",
          standard_ref: 'ת"י 1555',
          status: "UNCHECKED",
          notes: "לא נגיש",
          photo_ids: [],
          sort_order: 0,
        },
        {
          id: "checklist-2",
          catalog_issue_id: "SUP-FIN-005",
          issue_name_he: "חלון",
          category_id: "DOORS",
          category_name_he: "חלונות",
          top_family: "FINISHING_WORKS",
          standard_ref: 'ת"י 1090',
          status: "OK",
          photo_ids: [],
          sort_order: 1,
        },
      ])
    );

    expect(result).toEqual({ ok: true });
  });
});
