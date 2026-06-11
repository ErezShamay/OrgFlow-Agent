"use client";

import type { ChecklistBlock, ChecklistItem } from "@/lib/field-reports/schema/types";
import { FR_TOUCH_TEXTAREA } from "@/lib/field-reports/touch-input-class";

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

  function patchItem(itemId: string, patch: Partial<ChecklistItem>) {
    onChange({
      ...block,
      items: block.items.map((item) =>
        item.id === itemId ? { ...item, ...patch } : item
      ),
    });
  }

  if (items.length === 0) {
    return (
      <p className="text-sm text-zinc-500">
        אין פריטים בצ&apos;קליסט - טען תבנית גמר או הוסף סעיף צ&apos;קליסט מחדש.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li
          key={item.id}
          className="space-y-2 rounded-lg border border-zinc-100 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950"
        >
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
            <span className="font-medium leading-snug">{item.label_he}</span>
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
  );
}
