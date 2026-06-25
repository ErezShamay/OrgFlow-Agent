"use client";

import Button from "@/components/ui/Button";
import {
  addChecklistItem,
  confirmChecklistItemDelete,
  removeChecklistItem,
  shouldConfirmFinishingChecklistItemDelete,
  updateChecklistItem,
} from "@/lib/field-reports/schema/checklist-item-mutations";
import type { ChecklistBlock, ChecklistItem } from "@/lib/field-reports/schema/types";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
  FR_TOUCH_TEXTAREA,
} from "@/lib/field-reports/touch-input-class";

type ReportChecklistBlockEditorProps = {
  block: ChecklistBlock;
  disabled: boolean;
  onChange: (block: ChecklistBlock) => void;
};

function sortedItems(items: ChecklistItem[]): ChecklistItem[] {
  return [...items].sort(
    (left, right) => (left.sort_order ?? 0) - (right.sort_order ?? 0)
  );
}

export default function ReportChecklistBlockEditor({
  block,
  disabled,
  onChange,
}: ReportChecklistBlockEditorProps) {
  const items = sortedItems(block.items);

  function replaceItems(nextItems: ChecklistItem[]) {
    onChange({ ...block, items: nextItems });
  }

  function patchItem(itemId: string, patch: Partial<ChecklistItem>) {
    replaceItems(updateChecklistItem(block.items, itemId, patch));
  }

  function handleAddItem() {
    replaceItems(addChecklistItem(block.items));
  }

  function handleRemoveItem(item: ChecklistItem) {
    if (
      shouldConfirmFinishingChecklistItemDelete(item)
      && !confirmChecklistItemDelete(
        "להסיר את הפריט? יש בו סימון או הערות."
      )
    ) {
      return;
    }
    replaceItems(removeChecklistItem(block.items, item.id));
  }

  return (
    <div className="space-y-3">
      {items.length === 0 ? (
        <p className="text-sm text-zinc-500">
          אין פריטים בצ&apos;קליסט — הוסף פריט או טען תבנית לפי סוג הביקור.
        </p>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li
              key={item.id}
              className="space-y-2 rounded-lg border border-zinc-100 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <label className="block min-w-0 flex-1 space-y-1 text-sm">
                  <span className="font-medium text-zinc-600">שם הפריט</span>
                  <input
                    className={FR_TOUCH_INPUT}
                    value={item.label_he}
                    disabled={disabled}
                    placeholder="למשל: בדיקת מעליות"
                    onChange={(event) =>
                      patchItem(item.id, { label_he: event.target.value })
                    }
                  />
                </label>
                {disabled ? null : (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    className={FR_TOUCH_BUTTON}
                    onClick={() => handleRemoveItem(item)}
                  >
                    הסר
                  </Button>
                )}
              </div>
              <label className="flex cursor-pointer items-start gap-3 text-sm">
                <input
                  type="checkbox"
                  className="mt-1 size-5 shrink-0"
                  checked={item.checked}
                  disabled={disabled}
                  onChange={(event) =>
                    patchItem(item.id, { checked: event.target.checked })
                  }
                />
                <span className="font-medium leading-snug">בוצע</span>
              </label>
              <label className="block space-y-1 text-sm">
                <span className="text-zinc-600">הערות</span>
                <textarea
                  className={FR_TOUCH_TEXTAREA}
                  rows={2}
                  value={item.notes ?? ""}
                  disabled={disabled}
                  placeholder="הערות לפריט (אופציונלי)"
                  onChange={(event) =>
                    patchItem(item.id, {
                      notes: event.target.value.trim() || null,
                    })
                  }
                />
              </label>
            </li>
          ))}
        </ul>
      )}

      {disabled ? null : (
        <Button
          type="button"
          variant="secondary"
          className={FR_TOUCH_BUTTON}
          onClick={handleAddItem}
        >
          הוסף פריט
        </Button>
      )}
    </div>
  );
}
