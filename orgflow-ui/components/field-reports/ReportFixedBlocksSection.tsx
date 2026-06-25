"use client";

import Button from "@/components/ui/Button";
import {
  buildFixedTextBlocksForNewReport,
  createEmptyCustomFixedTextBlock,
  FIXED_TEXT_BLOCK_KIND_LABELS,
  isRemovableFixedTextBlock,
} from "@/lib/field-reports/schema/fixed-text-inject";
import type { FixedTextBlock, FixedTextBlockKind } from "@/lib/field-reports/schema/types";
import {
  patchHeaderFieldsFixedTextBlocks,
  type ReportHeaderFields,
} from "@/lib/field-reports/header-fields";
import {
  normalizeOptionalTextInput,
  optionalTextForSave,
  UNSPECIFIED_FIELD_LABEL_HE,
} from "@/lib/validation/optional-field-display";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_TEXTAREA,
} from "@/lib/field-reports/touch-input-class";

type ReportFixedBlocksSectionProps = {
  fields: ReportHeaderFields;
  visitType: string;
  visitDate: string;
  disabled: boolean;
  onChange: (fields: ReportHeaderFields) => void;
};

export default function ReportFixedBlocksSection({
  fields,
  visitType,
  visitDate,
  disabled,
  onChange,
}: ReportFixedBlocksSectionProps) {
  const blocks =
    fields.fixed_text_blocks.length > 0
      ? fields.fixed_text_blocks
      : buildFixedTextBlocksForNewReport({ visitDate });

  function applyUpdate(update: {
    fixed_text_blocks?: FixedTextBlock[];
    include_fixed_text_blocks?: boolean;
  }) {
    onChange(
      patchHeaderFieldsFixedTextBlocks(
        fields,
        {
          fixed_text_blocks: update.fixed_text_blocks ?? blocks,
          include_fixed_text_blocks:
            update.include_fixed_text_blocks ?? fields.include_fixed_text_blocks,
        },
        visitType,
        visitDate
      )
    );
  }

  function updateBlock(blockId: string, patch: Partial<FixedTextBlock>) {
    applyUpdate({
      fixed_text_blocks: blocks.map((block) =>
        block.id === blockId ? { ...block, ...patch } : block
      ),
    });
  }

  function restoreDefaults() {
    applyUpdate({
      fixed_text_blocks: buildFixedTextBlocksForNewReport({
        visitDate,
        includeBoilerplate: true,
      }),
      include_fixed_text_blocks: true,
    });
  }

  function handleAddCustomBlock() {
    const nextSortOrder = blocks.reduce(
      (max, block) => Math.max(max, block.sort_order ?? 0),
      -1
    );
    applyUpdate({
      fixed_text_blocks: [
        ...blocks,
        createEmptyCustomFixedTextBlock(nextSortOrder + 1),
      ],
    });
  }

  function handleRemoveCustomBlock(block: FixedTextBlock) {
    const hasContent =
      Boolean(block.title_he?.trim()) || Boolean(block.body_he.trim());
    if (
      hasContent
      && !window.confirm("להסיר את סעיף הטקסט המותאם?")
    ) {
      return;
    }
    applyUpdate({
      fixed_text_blocks: blocks.filter((entry) => entry.id !== block.id),
    });
  }

  return (
    <section className="space-y-4 rounded-xl border border-zinc-200 p-4 md:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">טקסטים קבועים לדוח</h2>
          <p className="mt-1 text-sm text-zinc-500">
            disclaimers, המלצות חורף (אוקטובר–מרץ) והערות - יופיעו ב-PDF לפני
            החתימה.
          </p>
        </div>
        {disabled ? null : (
          <Button
            type="button"
            variant="secondary"
            className={FR_TOUCH_BUTTON}
            onClick={() => restoreDefaults()}
          >
            שחזר תבניות
          </Button>
        )}
      </div>

      <label className="flex items-center gap-3 text-sm font-medium">
        <input
          type="checkbox"
          className="size-5 rounded border-zinc-300"
          checked={fields.include_fixed_text_blocks}
          disabled={disabled}
          onChange={(event) =>
            applyUpdate({ include_fixed_text_blocks: event.target.checked })
          }
        />
        <span>כלול טקסטים קבועים בדוח (PDF)</span>
      </label>

      <ul className="space-y-4">
        {blocks.map((block) => (
          <li
            key={block.id}
            className="space-y-2 rounded-lg border border-zinc-100 bg-zinc-50/60 p-3 dark:border-zinc-800 dark:bg-zinc-900/30"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <label className="flex items-center gap-2 text-sm font-medium">
                <input
                  type="checkbox"
                  className="size-4 rounded border-zinc-300"
                  checked={block.enabled}
                  disabled={disabled || !fields.include_fixed_text_blocks}
                  onChange={(event) =>
                    updateBlock(block.id, { enabled: event.target.checked })
                  }
                />
                <span>{blockLabel(block)}</span>
              </label>
              {disabled || !isRemovableFixedTextBlock(block) ? null : (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  className={FR_TOUCH_BUTTON}
                  onClick={() => handleRemoveCustomBlock(block)}
                >
                  הסר סעיף
                </Button>
              )}
            </div>

            {block.kind === "custom"
            || block.title_he !== null && block.title_he !== undefined ? (
              <label className="block space-y-1 text-sm">
                <span className="text-zinc-600">כותרת (אופציונלי)</span>
                <input
                  className="of-input w-full"
                  value={block.title_he ?? ""}
                  disabled={disabled}
                  onChange={(event) =>
                    updateBlock(block.id, {
                      title_he: event.target.value || null,
                    })
                  }
                />
              </label>
            ) : null}

            <label className="block space-y-1 text-sm">
              <span className="text-zinc-600">תוכן</span>
              <textarea
                className={`of-input min-h-24 w-full ${FR_TOUCH_TEXTAREA}`}
                value={block.body_he}
                disabled={disabled}
                onChange={(event) =>
                  updateBlock(block.id, { body_he: event.target.value })
                }
              />
            </label>
          </li>
        ))}
      </ul>

      {disabled ? null : (
        <Button
          type="button"
          variant="secondary"
          className={FR_TOUCH_BUTTON}
          onClick={handleAddCustomBlock}
        >
          הוסף סעיף טקסט
        </Button>
      )}

      <ProjectUpdatesEditor
        items={fields.project_updates}
        disabled={disabled}
        onChange={(project_updates) => onChange({ ...fields, project_updates })}
      />

      <StringListEditor
        label="הערות נוספות לקבלן"
        items={fields.contractor_notes}
        disabled={disabled}
        placeholder="הערה לקבלן"
        onChange={(contractor_notes) => onChange({ ...fields, contractor_notes })}
      />

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block space-y-1 text-sm">
          <span className="font-medium">תואר מפקח (בחתימה)</span>
          <input
            className="of-input w-full"
            value={normalizeOptionalTextInput(fields.inspector_title)}
            disabled={disabled}
            placeholder="למשל: מפקח בכיר"
            onChange={(event) =>
              onChange({
                ...fields,
                inspector_title:
                  optionalTextForSave(event.target.value) ?? "",
              })
            }
          />
        </label>
        <label className="block space-y-1 text-sm">
          <span className="font-medium">מספר רישוי (בחתימה)</span>
          <input
            className="of-input w-full"
            value={normalizeOptionalTextInput(fields.inspector_license)}
            disabled={disabled}
            placeholder={UNSPECIFIED_FIELD_LABEL_HE}
            onChange={(event) =>
              onChange({
                ...fields,
                inspector_license:
                  optionalTextForSave(event.target.value) ?? "",
              })
            }
          />
        </label>
      </div>
    </section>
  );
}

function blockLabel(block: FixedTextBlock): string {
  return (
    block.title_he?.trim()
    || FIXED_TEXT_BLOCK_KIND_LABELS[block.kind as FixedTextBlockKind]
  );
}

function StringListEditor({
  label,
  items,
  disabled,
  placeholder,
  onChange,
}: {
  label: string;
  items: string[];
  disabled: boolean;
  placeholder: string;
  onChange: (items: string[]) => void;
}) {
  const rows = items.length ? items : [""];

  function updateItem(index: number, value: string) {
    const next = [...rows];
    next[index] = value;
    onChange(next);
  }

  function addItem() {
    onChange([...rows, ""]);
  }

  function removeItem(index: number) {
    const next = rows.filter((_, itemIndex) => itemIndex !== index);
    onChange(next.length ? next : [""]);
  }

  return (
    <div className="space-y-2">
      <span className="text-sm font-medium">{label}</span>
      <ul className="space-y-2">
        {rows.map((item, index) => (
          <li
            key={`${label}-${index}`}
            className="flex flex-wrap items-center gap-2"
          >
            <span className="w-6 text-sm text-zinc-500">{index + 1}.</span>
            <input
              className="of-input min-w-0 flex-1"
              value={item}
              disabled={disabled}
              placeholder={placeholder}
              onChange={(event) => updateItem(index, event.target.value)}
            />
            {disabled ? null : (
              <Button
                type="button"
                variant="secondary"
                disabled={rows.length === 1 && !item.trim()}
                onClick={() => removeItem(index)}
              >
                הסר
              </Button>
            )}
          </li>
        ))}
      </ul>
      {disabled ? null : (
        <Button type="button" variant="secondary" onClick={addItem}>
          הוסף שורה
        </Button>
      )}
    </div>
  );
}

function ProjectUpdatesEditor({
  items,
  disabled,
  onChange,
}: {
  items: string[];
  disabled: boolean;
  onChange: (items: string[]) => void;
}) {
  const rows = items.length ? items : [""];

  function updateItem(index: number, value: string) {
    const next = [...rows];
    next[index] = value;
    onChange(next);
  }

  function addItem() {
    onChange([...rows, ""]);
  }

  function removeItem(index: number) {
    const next = rows.filter((_, itemIndex) => itemIndex !== index);
    onChange(next.length ? next : [""]);
  }

  return (
    <div className="space-y-2">
      <span className="text-sm font-medium">עדכונים לפרויקט (כותרת PDF)</span>
      <ul className="space-y-2">
        {rows.map((item, index) => (
          <li
            key={`project-update-${index}`}
            className="flex flex-wrap items-center gap-2"
          >
            <span className="w-6 text-sm text-zinc-500">{index + 1}.</span>
            <input
              className="of-input min-w-0 flex-1"
              value={item}
              disabled={disabled}
              placeholder="עדכון לפרויקט"
              onChange={(event) => updateItem(index, event.target.value)}
            />
            {disabled ? null : (
              <Button
                type="button"
                variant="secondary"
                disabled={rows.length === 1 && !item.trim()}
                onClick={() => removeItem(index)}
              >
                הסר
              </Button>
            )}
          </li>
        ))}
      </ul>
      {disabled ? null : (
        <Button type="button" variant="secondary" onClick={addItem}>
          הוסף שורה
        </Button>
      )}
    </div>
  );
}
