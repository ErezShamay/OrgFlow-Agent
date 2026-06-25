import { describe, expect, it } from "vitest";

import { createEmptyBlockForKind } from "@/lib/field-reports/schema/blocks-storage";
import {
  addChecklistItem,
  addCustomSupervisionItem,
  createEmptyChecklistItem,
  hiddenSupervisionCatalogItems,
  hideSupervisionCatalogItem,
  removeChecklistItem,
  removeSupervisionCustomItem,
  restoreSupervisionCatalogItem,
  shouldConfirmFinishingChecklistItemDelete,
  visibleSupervisionChecklistItems,
} from "@/lib/field-reports/schema/checklist-item-mutations";
import type { SupervisionChecklistItem } from "@/lib/field-reports/schema/types";

describe("checklist-item-mutations", () => {
  it("creates finishing checklist block with one empty item", () => {
    const block = createEmptyBlockForKind("checklist", "FINISHING_APARTMENTS");
    expect(block.kind).toBe("checklist");
    if (block.kind !== "checklist") {
      throw new Error("expected checklist block");
    }
    expect(block.items).toHaveLength(1);
    expect(block.items[0].label_he).toBe("");
  });

  it("adds and removes finishing checklist items with sort_order", () => {
    const first = createEmptyChecklistItem(0);
    const second = addChecklistItem([first]);
    expect(second).toHaveLength(2);
    expect(second[1].sort_order).toBe(1);

    const removed = removeChecklistItem(second, second[0].id);
    expect(removed).toHaveLength(1);
    expect(removed[0].sort_order).toBe(0);
  });

  it("requires confirm when finishing item has content", () => {
    expect(
      shouldConfirmFinishingChecklistItemDelete({
        id: "a",
        label_he: "חשמל",
        checked: true,
        notes: null,
      })
    ).toBe(true);
    expect(
      shouldConfirmFinishingChecklistItemDelete({
        id: "b",
        label_he: "",
        checked: false,
        notes: null,
      })
    ).toBe(false);
  });

  it("hides catalog supervision items without deleting them", () => {
    const catalogItem: SupervisionChecklistItem = {
      id: "cat-1",
      catalog_issue_id: "ISSUE-1",
      issue_name_he: "איטום",
      category_id: "cat",
      category_name_he: "איטום",
      top_family: "SYSTEM_WATERPROOFING_AND_INSULATION",
      standard_ref: "ת\"י 123",
      status: "OK",
      notes: null,
      photo_ids: [],
      sort_order: 0,
    };

    const hidden = hideSupervisionCatalogItem([catalogItem], catalogItem.id);
    expect(hidden).toHaveLength(1);
    expect(hidden[0].hidden).toBe(true);
    expect(visibleSupervisionChecklistItems(hidden)).toHaveLength(0);
    expect(hiddenSupervisionCatalogItems(hidden)).toHaveLength(1);

    const restored = restoreSupervisionCatalogItem(hidden, catalogItem.id);
    expect(visibleSupervisionChecklistItems(restored)).toHaveLength(1);
  });

  it("adds and removes custom supervision items", () => {
    const withCustom = addCustomSupervisionItem([]);
    expect(withCustom).toHaveLength(1);
    expect(withCustom[0].is_custom).toBe(true);

    withCustom[0] = { ...withCustom[0], issue_name_he: "מיזוג" };
    const removed = removeSupervisionCustomItem(withCustom, withCustom[0].id);
    expect(removed).toHaveLength(0);
  });
});
