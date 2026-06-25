import type {
  ChecklistItemStatus,
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
} from "@/lib/field-reports/schema/types";
import { CHECKLIST_ITEM_STATUSES } from "@/lib/field-reports/schema/types";

export const CHECKLIST_ITEM_STATUS_LABELS: Record<ChecklistItemStatus, string> = {
  UNCHECKED: "לא נבדק",
  OK: "תקין",
  DEFECT: "ליקוי",
  NOT_APPLICABLE: "לא רלוונטי",
};

export function checklistItemStatusLabelHe(
  status: ChecklistItemStatus
): string {
  return CHECKLIST_ITEM_STATUS_LABELS[status];
}

export const CHECKLIST_ITEM_STATUS_OPTIONS = CHECKLIST_ITEM_STATUSES.map(
  (status) => ({
    value: status,
    label_he: CHECKLIST_ITEM_STATUS_LABELS[status],
  })
);

export type SupervisionChecklistGroup = {
  top_family: string;
  top_family_label_he: string;
  categories: Array<{
    category_id: string;
    category_name_he: string;
    items: SupervisionChecklistItem[];
  }>;
};

export function groupSupervisionChecklistItems(
  block: SupervisionChecklistBlock,
  familyLabel: (topFamily: string) => string
): SupervisionChecklistGroup[] {
  const byFamily = new Map<string, SupervisionChecklistGroup>();

  for (const item of [...block.items].sort(
    (left, right) => left.sort_order - right.sort_order
  )) {
    if (item.hidden) {
      continue;
    }
    let family = byFamily.get(item.top_family);
    if (!family) {
      family = {
        top_family: item.top_family,
        top_family_label_he: familyLabel(item.top_family),
        categories: [],
      };
      byFamily.set(item.top_family, family);
    }

    let category = family.categories.find(
      (entry) => entry.category_id === item.category_id
    );
    if (!category) {
      category = {
        category_id: item.category_id,
        category_name_he: item.category_name_he,
        items: [],
      };
      family.categories.push(category);
    }

    category.items.push(item);
  }

  return [...byFamily.values()];
}

