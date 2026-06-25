"use client";

import { useMemo, useState } from "react";

import SupervisionChecklistItemPhotoCapture from "@/components/field-reports/supervision/ChecklistItemPhotoCapture";
import QuickInspectToggle from "@/components/field-reports/supervision/QuickInspectToggle";
import Button from "@/components/ui/Button";
import { catalogFamilyLabelHe } from "@/lib/field-reports/catalog-labels";
import {
  addCustomSupervisionItem,
  confirmChecklistItemDelete,
  hiddenSupervisionCatalogItems,
  hideSupervisionCatalogItem,
  isSupervisionCatalogItem,
  isSupervisionCustomItem,
  removeSupervisionCustomItem,
  restoreSupervisionCatalogItem,
  shouldConfirmSupervisionChecklistItemDelete,
  updateSupervisionChecklistItem,
  visibleSupervisionChecklistItems,
} from "@/lib/field-reports/schema/checklist-item-mutations";
import type {
  ChecklistItemStatus,
  InspectMode,
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
} from "@/lib/field-reports/schema/types";
import {
  CHECKLIST_ITEM_STATUS_OPTIONS,
  groupSupervisionChecklistItems,
} from "@/lib/field-reports/supervision-labels";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
  FR_TOUCH_NOTES,
} from "@/lib/field-reports/touch-input-class";

type SupervisionChecklistEditorProps = {
  block: SupervisionChecklistBlock;
  reportId: string;
  inspectMode?: InspectMode;
  disabled?: boolean;
  onChange: (block: SupervisionChecklistBlock) => void;
};

function replaceItems(
  block: SupervisionChecklistBlock,
  items: SupervisionChecklistItem[]
): SupervisionChecklistBlock {
  return { ...block, items };
}

export default function SupervisionChecklistEditor({
  block,
  reportId,
  inspectMode = "standard",
  disabled = false,
  onChange,
}: SupervisionChecklistEditorProps) {
  const isQuickInspect = inspectMode === "quick";
  const visibleItems = useMemo(
    () => visibleSupervisionChecklistItems(block.items),
    [block.items]
  );
  const hiddenCatalogItems = useMemo(
    () => hiddenSupervisionCatalogItems(block.items),
    [block.items]
  );
  const groups = useMemo(
    () =>
      groupSupervisionChecklistItems(
        { ...block, items: visibleItems },
        (topFamily) => catalogFamilyLabelHe(topFamily)
      ),
    [block, visibleItems]
  );
  const [openFamily, setOpenFamily] = useState<string | null>(
    groups[0]?.top_family ?? null
  );
  const [hiddenOpen, setHiddenOpen] = useState(false);

  function patchItems(
    updater: (items: SupervisionChecklistItem[]) => SupervisionChecklistItem[]
  ) {
    onChange(replaceItems(block, updater(block.items)));
  }

  function patchItem(
    itemId: string,
    patch: Partial<SupervisionChecklistItem>
  ) {
    patchItems((items) => updateSupervisionChecklistItem(items, itemId, patch));
  }

  function setItemStatus(itemId: string, status: ChecklistItemStatus) {
    patchItem(itemId, { status });
  }

  function handleAddCustomItem() {
    patchItems((items) => addCustomSupervisionItem(items));
  }

  function handleHideCatalogItem(item: SupervisionChecklistItem) {
    if (
      shouldConfirmSupervisionChecklistItemDelete(item)
      && !confirmChecklistItemDelete(
        "להסתיר את הפריט? יש בו סימון, הערות או תמונות."
      )
    ) {
      return;
    }
    patchItems((items) => hideSupervisionCatalogItem(items, item.id));
  }

  function handleRemoveCustomItem(item: SupervisionChecklistItem) {
    if (
      shouldConfirmSupervisionChecklistItemDelete(item)
      && !confirmChecklistItemDelete("להסיר את הפריט המותאם?")
    ) {
      return;
    }
    patchItems((items) => removeSupervisionCustomItem(items, item.id));
  }

  function renderItemControls(item: SupervisionChecklistItem) {
    if (disabled) {
      return null;
    }

    if (isSupervisionCatalogItem(item)) {
      return (
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className={FR_TOUCH_BUTTON}
          onClick={() => handleHideCatalogItem(item)}
        >
          הסתר
        </Button>
      );
    }

    return (
      <Button
        type="button"
        variant="secondary"
        size="sm"
        className={FR_TOUCH_BUTTON}
        onClick={() => handleRemoveCustomItem(item)}
      >
        הסר
      </Button>
    );
  }

  function renderItemBody(item: SupervisionChecklistItem) {
    return (
      <>
        <div className="flex flex-wrap items-start justify-between gap-2">
          {isSupervisionCustomItem(item) ? (
            <label className="block min-w-0 flex-1 space-y-1 text-sm">
              <span className="font-medium text-zinc-600">שם הפריט</span>
              <input
                className={FR_TOUCH_INPUT}
                value={item.issue_name_he}
                disabled={disabled}
                placeholder="פריט מותאם"
                onChange={(event) =>
                  patchItem(item.id, { issue_name_he: event.target.value })
                }
              />
            </label>
          ) : (
            <div>
              <p className="font-medium leading-snug">{item.issue_name_he}</p>
              <p className="mt-1 text-xs text-zinc-500">{item.standard_ref}</p>
            </div>
          )}
          {renderItemControls(item)}
        </div>

        {isQuickInspect ? (
          <QuickInspectToggle
            status={item.status}
            disabled={disabled}
            onStatusChange={(status) => setItemStatus(item.id, status)}
          />
        ) : (
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
                  onClick={() => setItemStatus(item.id, option.value)}
                >
                  {option.label_he}
                </button>
              );
            })}
          </div>
        )}

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
                notes: event.target.value.trim() || null,
              })
            }
          />
        </label>

        <SupervisionChecklistItemPhotoCapture
          status={item.status}
          reportId={reportId}
          checklistItemId={item.id}
          photoIds={item.photo_ids}
          disabled={disabled}
          onPhotoIdsChange={(photo_ids) => patchItem(item.id, { photo_ids })}
        />
      </>
    );
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
          {visibleItems.length} פריטי בדיקה · {groups.length} מלאכות
          {hiddenCatalogItems.length
            ? ` · ${hiddenCatalogItems.length} מוסתרים`
            : ""}
          {isQuickInspect ? " · מצב סימון מהיר (V/X)" : null}
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
                            {renderItemBody(item)}
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

      {hiddenCatalogItems.length > 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-300 dark:border-zinc-700">
          <button
            type="button"
            className={`flex w-full items-center justify-between px-4 py-3 text-right text-sm ${FR_TOUCH_BUTTON}`}
            onClick={() => setHiddenOpen((current) => !current)}
          >
            <span>פריטים מוסתרים ({hiddenCatalogItems.length})</span>
            <span className="text-zinc-500">{hiddenOpen ? "▲" : "▼"}</span>
          </button>
          {hiddenOpen ? (
            <ul className="space-y-2 border-t border-zinc-200 px-4 py-3 dark:border-zinc-800">
              {hiddenCatalogItems.map((item) => (
                <li
                  key={item.id}
                  className="flex flex-wrap items-center justify-between gap-2 text-sm"
                >
                  <span>{item.issue_name_he}</span>
                  {disabled ? null : (
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      className={FR_TOUCH_BUTTON}
                      onClick={() =>
                        patchItems((items) =>
                          restoreSupervisionCatalogItem(items, item.id)
                        )
                      }
                    >
                      שחזר
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {disabled ? null : (
        <Button
          type="button"
          variant="secondary"
          className={FR_TOUCH_BUTTON}
          onClick={handleAddCustomItem}
        >
          הוסף פריט מותאם
        </Button>
      )}
    </section>
  );
}
