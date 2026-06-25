/**
 * CRUD helpers for checklist items (MOD-00 / PRD-REPORT-MODULARITY-001).
 */

import type {
  ChecklistItem,
  ChecklistItemStatus,
  SupervisionChecklistItem,
} from "./types";

export const CUSTOM_SUPERVISION_TOP_FAMILY = "CUSTOM";
export const CUSTOM_SUPERVISION_CATEGORY_ID = "custom-items";
export const CUSTOM_SUPERVISION_CATEGORY_NAME_HE = "פריטים מותאמים";

function nextItemId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function reindexSortOrder<T extends { sort_order?: number }>(items: T[]): T[] {
  return items.map((item, index) => ({
    ...item,
    sort_order: index,
  }));
}

export function createEmptyChecklistItem(sortOrder = 0): ChecklistItem {
  return {
    id: nextItemId("checklist-item"),
    label_he: "",
    checked: false,
    notes: null,
    sort_order: sortOrder,
  };
}

export function addChecklistItem(
  items: ChecklistItem[],
  item?: ChecklistItem
): ChecklistItem[] {
  const next = item ?? createEmptyChecklistItem(items.length);
  return reindexSortOrder([...items, { ...next, sort_order: items.length }]);
}

export function updateChecklistItem(
  items: ChecklistItem[],
  itemId: string,
  patch: Partial<ChecklistItem>
): ChecklistItem[] {
  return items.map((item) =>
    item.id === itemId ? { ...item, ...patch } : item
  );
}

export function removeChecklistItem(
  items: ChecklistItem[],
  itemId: string
): ChecklistItem[] {
  return reindexSortOrder(items.filter((item) => item.id !== itemId));
}

export function shouldConfirmFinishingChecklistItemDelete(
  item: ChecklistItem
): boolean {
  return item.checked || Boolean(item.notes?.trim());
}

export function isSupervisionCustomItem(
  item: SupervisionChecklistItem
): boolean {
  return item.is_custom === true;
}

export function isSupervisionCatalogItem(
  item: SupervisionChecklistItem
): boolean {
  return !isSupervisionCustomItem(item);
}

export function visibleSupervisionChecklistItems(
  items: SupervisionChecklistItem[]
): SupervisionChecklistItem[] {
  return items.filter((item) => {
    if (item.hidden) {
      return false;
    }
    if (isSupervisionCustomItem(item) && !item.issue_name_he.trim()) {
      return false;
    }
    return true;
  });
}

export function hiddenSupervisionCatalogItems(
  items: SupervisionChecklistItem[]
): SupervisionChecklistItem[] {
  return items.filter((item) => item.hidden && isSupervisionCatalogItem(item));
}

export function createEmptyCustomSupervisionItem(
  sortOrder: number
): SupervisionChecklistItem {
  return {
    id: nextItemId("custom-supervision"),
    catalog_issue_id: "",
    issue_name_he: "",
    category_id: CUSTOM_SUPERVISION_CATEGORY_ID,
    category_name_he: CUSTOM_SUPERVISION_CATEGORY_NAME_HE,
    top_family: CUSTOM_SUPERVISION_TOP_FAMILY,
    standard_ref: "",
    status: "UNCHECKED",
    notes: null,
    photo_ids: [],
    sort_order: sortOrder,
    is_custom: true,
    hidden: false,
  };
}

export function addCustomSupervisionItem(
  items: SupervisionChecklistItem[]
): SupervisionChecklistItem[] {
  return reindexSortOrder([
    ...items,
    createEmptyCustomSupervisionItem(items.length),
  ]);
}

export function updateSupervisionChecklistItem(
  items: SupervisionChecklistItem[],
  itemId: string,
  patch: Partial<SupervisionChecklistItem>
): SupervisionChecklistItem[] {
  return items.map((item) =>
    item.id === itemId ? { ...item, ...patch } : item
  );
}

export function hideSupervisionCatalogItem(
  items: SupervisionChecklistItem[],
  itemId: string
): SupervisionChecklistItem[] {
  return updateSupervisionChecklistItem(items, itemId, { hidden: true });
}

export function restoreSupervisionCatalogItem(
  items: SupervisionChecklistItem[],
  itemId: string
): SupervisionChecklistItem[] {
  return updateSupervisionChecklistItem(items, itemId, { hidden: false });
}

export function removeSupervisionCustomItem(
  items: SupervisionChecklistItem[],
  itemId: string
): SupervisionChecklistItem[] {
  return reindexSortOrder(
    items.filter((item) => item.id !== itemId || isSupervisionCatalogItem(item))
  );
}

export function shouldConfirmSupervisionChecklistItemDelete(
  item: SupervisionChecklistItem
): boolean {
  if (item.notes?.trim()) {
    return true;
  }
  if (item.photo_ids.length > 0) {
    return true;
  }
  const status = item.status as ChecklistItemStatus;
  return status !== "UNCHECKED";
}

export function confirmChecklistItemDelete(message: string): boolean {
  return window.confirm(message);
}
