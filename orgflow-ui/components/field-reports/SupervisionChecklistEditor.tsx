"use client";

import { useMemo, useState } from "react";

import ChecklistItemPhotoCapture from "@/components/field-reports/ChecklistItemPhotoCapture";
import { catalogFamilyLabelHe } from "@/lib/field-reports/catalog-labels";
import type {
  ChecklistItemStatus,
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
} from "@/lib/field-reports/schema/types";
import {
  CHECKLIST_ITEM_STATUS_OPTIONS,
  groupSupervisionChecklistItems,
} from "@/lib/field-reports/supervision-labels";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_NOTES,
} from "@/lib/field-reports/touch-input-class";

type SupervisionChecklistEditorProps = {
  block: SupervisionChecklistBlock;
  reportId: string;
  disabled?: boolean;
  onChange: (block: SupervisionChecklistBlock) => void;
};

export default function SupervisionChecklistEditor({
  block,
  reportId,
  disabled = false,
  onChange,
}: SupervisionChecklistEditorProps) {
  const groups = useMemo(
    () =>
      groupSupervisionChecklistItems(block, (topFamily) =>
        catalogFamilyLabelHe(topFamily)
      ),
    [block]
  );
  const [openFamily, setOpenFamily] = useState<string | null>(
    groups[0]?.top_family ?? null
  );

  function patchItem(
    itemId: string,
    patch: Partial<SupervisionChecklistItem>
  ) {
    onChange({
      ...block,
      items: block.items.map((item) =>
        item.id === itemId ? { ...item, ...patch } : item
      ),
    });
  }

  function setItemStatus(itemId: string, status: ChecklistItemStatus) {
    patchItem(itemId, { status });
  }

  if (!block.items.length) {
    return (
      <p className="text-sm text-zinc-500">
        אין פריטים בצ&apos;קליסט — בדוק את הגדרות הביקור.
      </p>
    );
  }

  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h2 className="text-lg font-semibold">{block.title_he}</h2>
        <p className="text-sm text-zinc-500">
          {block.items.length} פריטי בדיקה · {groups.length} מלאכות
        </p>
      </header>

      <div className="space-y-3">
        {groups.map((group) => {
          const isOpen = openFamily === group.top_family;

          return (
            <div
              key={group.top_family}
              className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800"
            >
              <button
                type="button"
                className={`flex w-full items-center justify-between px-4 py-3 text-right ${FR_TOUCH_BUTTON}`}
                onClick={() =>
                  setOpenFamily(isOpen ? null : group.top_family)
                }
              >
                <span className="font-medium">{group.top_family_label_he}</span>
                <span className="text-sm text-zinc-500">
                  {isOpen ? "▲" : "▼"}
                </span>
              </button>

              {isOpen ? (
                <div className="space-y-4 border-t border-zinc-200 px-4 py-4 dark:border-zinc-800">
                  {group.categories.map((category) => (
                    <div key={category.category_id} className="space-y-3">
                      <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                        {category.category_name_he}
                      </h3>
                      <ul className="space-y-3">
                        {category.items.map((item) => (
                          <li
                            key={item.id}
                            className="space-y-3 rounded-lg border border-zinc-100 bg-zinc-50/80 p-3 dark:border-zinc-800 dark:bg-zinc-900/40"
                          >
                            <div className="flex flex-wrap items-start justify-between gap-2">
                              <div>
                                <p className="font-medium leading-snug">
                                  {item.issue_name_he}
                                </p>
                                <p className="mt-1 text-xs text-zinc-500">
                                  {item.standard_ref}
                                </p>
                              </div>
                            </div>

                            <div className="flex flex-wrap gap-2">
                              {CHECKLIST_ITEM_STATUS_OPTIONS.map((option) => {
                                const selected = item.status === option.value;

                                return (
                                  <button
                                    key={option.value}
                                    type="button"
                                    disabled={disabled}
                                    aria-pressed={selected}
                                    className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                                      selected
                                        ? "bg-brand text-white dark:bg-brand-light dark:text-brand-dark"
                                        : "border border-zinc-200 bg-white text-zinc-700 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-200"
                                    }`}
                                    onClick={() =>
                                      setItemStatus(item.id, option.value)
                                    }
                                  >
                                    {option.label_he}
                                  </button>
                                );
                              })}
                            </div>

                            <label className="block space-y-1 text-sm">
                              <span className="text-zinc-600">הערות</span>
                              <textarea
                                className={FR_TOUCH_NOTES}
                                rows={2}
                                value={item.notes ?? ""}
                                disabled={disabled}
                                placeholder="הערות לפריט"
                                onChange={(event) =>
                                  patchItem(item.id, {
                                    notes:
                                      event.target.value.trim() || null,
                                  })
                                }
                              />
                            </label>

                            <ChecklistItemPhotoCapture
                              reportId={reportId}
                              checklistItemId={item.id}
                              photoIds={item.photo_ids}
                              disabled={disabled}
                              onPhotoIdsChange={(photo_ids) =>
                                patchItem(item.id, { photo_ids })
                              }
                            />
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}
