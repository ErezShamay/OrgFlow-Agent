"use client";

import Button from "@/components/ui/Button";
import {
  defaultConstructionProgressRows,
  PROGRESS_STATUS_SUGGESTIONS,
} from "@/lib/field-reports/construction-progress";
import { COLUMN_PRESET_OPTIONS } from "@/lib/field-reports/block-kind-labels";
import { getColumnPreset } from "@/lib/field-reports/schema/column-presets";
import type {
  BlockColumnId,
  ColumnPresetKey,
  ProgressRow,
  ProgressTableBlock,
} from "@/lib/field-reports/schema/types";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
} from "@/lib/field-reports/touch-input-class";

type ReportProgressBlockEditorProps = {
  block: ProgressTableBlock;
  visitType: string;
  disabled: boolean;
  onChange: (block: ProgressTableBlock) => void;
};

function newProgressRowId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `progress-row-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function emptyProgressRow(sortOrder: number): ProgressRow {
  return {
    id: newProgressRowId(),
    description: "",
    status: "",
    completion_date: "",
    sort_order: sortOrder,
  };
}

const PROGRESS_ROW_FIELDS: Record<BlockColumnId, keyof ProgressRow> = {
  description: "description",
  status: "status",
  completion_date: "completion_date",
  location: "description",
  trade: "description",
  notes: "description",
  photos: "description",
  checklist_item: "description",
};

export default function ReportProgressBlockEditor({
  block,
  visitType,
  disabled,
  onChange,
}: ReportProgressBlockEditorProps) {
  const columns = getColumnPreset(block.column_preset);
  const tableRows =
    block.rows.length > 0 ? block.rows : [emptyProgressRow(0)];

  function emitRows(rows: ProgressRow[]) {
    onChange({
      ...block,
      rows: rows.map((row, index) => ({ ...row, sort_order: index })),
    });
  }

  function updateRow(
    index: number,
    field: keyof ProgressRow,
    value: string
  ) {
    const next = [...tableRows];
    next[index] = { ...next[index], [field]: value };
    emitRows(next);
  }

  function addRow() {
    emitRows([...tableRows, emptyProgressRow(tableRows.length)]);
  }

  function removeRow(index: number) {
    const next = tableRows.filter((_, rowIndex) => rowIndex !== index);
    emitRows(next.length ? next : [emptyProgressRow(0)]);
  }

  function restoreDefaults() {
    const defaults = defaultConstructionProgressRows(visitType);
    emitRows(
      defaults.map((row, index) => ({
        id: `default-progress-row-${index}`,
        description: row.description,
        status: row.status,
        completion_date: row.completion_date,
        sort_order: index,
      }))
    );
  }

  function setColumnPreset(column_preset: ColumnPresetKey) {
    onChange({ ...block, column_preset });
  }

  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2">
        <label className="block space-y-1 text-sm">
          <span className="font-medium">preset עמודות</span>
          <select
            className={FR_TOUCH_INPUT}
            value={block.column_preset}
            disabled={disabled}
            onChange={(event) =>
              setColumnPreset(event.target.value as ColumnPresetKey)
            }
          >
            {COLUMN_PRESET_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[32rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-zinc-200 text-right">
              {columns.map((column) => (
                <th key={column.id} className="px-2 py-2 font-medium">
                  {column.header_he}
                </th>
              ))}
              {disabled ? null : <th className="w-16 px-2 py-2" />}
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row, index) => (
              <tr
                key={row.id}
                className="border-b border-zinc-100 align-top"
              >
                {columns.map((column) => {
                  const field = PROGRESS_ROW_FIELDS[column.id];
                  if (!field || field === "id" || field === "sort_order") {
                    return (
                      <td key={column.id} className="px-2 py-2">
                        -
                      </td>
                    );
                  }

                  const value = String(row[field] ?? "");

                  return (
                    <td key={column.id} className="px-2 py-2">
                      <input
                        className="of-input w-full"
                        value={value}
                        disabled={disabled}
                        list={
                          field === "status"
                            ? "field-report-progress-status"
                            : undefined
                        }
                        onChange={(event) =>
                          updateRow(index, field, event.target.value)
                        }
                      />
                    </td>
                  );
                })}
                {disabled ? null : (
                  <td className="px-2 py-2">
                    <Button
                      type="button"
                      variant="secondary"
                      className={FR_TOUCH_BUTTON}
                      disabled={
                        tableRows.length === 1
                        && !row.description.trim()
                        && !row.status.trim()
                        && !row.completion_date.trim()
                      }
                      onClick={() => removeRow(index)}
                    >
                      הסר
                    </Button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <datalist id="field-report-progress-status">
        {PROGRESS_STATUS_SUGGESTIONS.map((status) => (
          <option key={status} value={status} />
        ))}
      </datalist>

      {disabled ? null : (
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            className={FR_TOUCH_BUTTON}
            onClick={addRow}
          >
            הוסף שורה
          </Button>
          <Button
            type="button"
            variant="secondary"
            className={FR_TOUCH_BUTTON}
            onClick={restoreDefaults}
          >
            שחזר תבנית ברירת מחדל
          </Button>
        </div>
      )}
    </div>
  );
}
