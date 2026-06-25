"use client";

import { Fragment } from "react";

import FindingSimilarIssuesHint from "@/components/quality-issues/FindingSimilarIssuesHint";
import Button from "@/components/ui/Button";
import { COLUMN_PRESET_OPTIONS } from "@/lib/field-reports/block-kind-labels";
import { getColumnPreset } from "@/lib/field-reports/schema/column-presets";
import type {
  BlockColumnId,
  ColumnPresetKey,
  FindingRow,
  FindingsTableBlock,
} from "@/lib/field-reports/schema/types";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
  FR_TOUCH_TEXTAREA,
} from "@/lib/field-reports/touch-input-class";

type ReportFindingsBlockEditorProps = {
  block: FindingsTableBlock;
  disabled: boolean;
  projectId?: string | null;
  organizationId?: string | null;
  reportId?: string | null;
  /** שורות נגזרות מ-report.lines - עריכה דרך «שורות ממצאים» (FR-2.1). */
  lineDerived?: boolean;
  linkingRowId?: string | null;
  onLinkRow?: (
    rowId: string,
    linkedIssueId: string | null
  ) => void | Promise<void>;
  onChange: (block: FindingsTableBlock) => void;
};

function newFindingRowId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `finding-row-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function emptyFindingRow(sortOrder: number): FindingRow {
  return {
    id: newFindingRowId(),
    location: "",
    trade: "",
    status: "",
    description: "",
    notes: "",
    sort_order: sortOrder,
  };
}

const FINDING_ROW_FIELDS: Partial<
  Record<BlockColumnId, keyof FindingRow>
> = {
  location: "location",
  trade: "trade",
  status: "status",
  description: "description",
  notes: "notes",
};

function FindingRowMatchHintRow({
  row,
  projectId,
  organizationId,
  reportId,
  disabled,
  linking,
  columnCount,
  onLinkIssue,
  onMarkNewIssue,
  onUnlinkIssue,
}: {
  row: FindingRow;
  projectId?: string | null;
  organizationId?: string | null;
  reportId?: string | null;
  disabled: boolean;
  linking?: boolean;
  columnCount: number;
  onLinkIssue?: (issueId: string) => void | Promise<void>;
  onMarkNewIssue?: () => void | Promise<void>;
  onUnlinkIssue?: () => void | Promise<void>;
}) {
  return (
    <tr className="border-b border-zinc-100">
      <td colSpan={columnCount} className="px-2 py-2">
        <FindingSimilarIssuesHint
          projectId={projectId}
          organizationId={organizationId}
          reportId={reportId}
          lineId={row.id}
          disabled={disabled}
          linkedIssueId={row.linked_issue_id}
          linking={linking}
          location={row.location}
          trade={row.trade}
          group_key={row.group_key}
          issue_id={row.issue_id}
          onLinkIssue={onLinkIssue}
          onMarkNewIssue={onMarkNewIssue}
          onUnlinkIssue={onUnlinkIssue}
        />
      </td>
    </tr>
  );
}

export default function ReportFindingsBlockEditor({
  block,
  disabled,
  projectId = null,
  organizationId = null,
  reportId = null,
  lineDerived = false,
  linkingRowId = null,
  onLinkRow,
  onChange,
}: ReportFindingsBlockEditorProps) {
  const columns = getColumnPreset(block.column_preset);
  const tableReadOnly = disabled || lineDerived;
  const tableRows = block.rows.length > 0 ? block.rows : [];

  function emitRows(rows: FindingRow[]) {
    onChange({
      ...block,
      rows: rows.map((row, index) => ({ ...row, sort_order: index })),
    });
  }

  function updateRow(
    index: number,
    field: keyof FindingRow,
    value: string
  ) {
    const next = [...tableRows];
    next[index] = { ...next[index], [field]: value };
    emitRows(next);
  }

  function addRow() {
    emitRows([...tableRows, emptyFindingRow(tableRows.length)]);
  }

  function removeRow(index: number) {
    emitRows(tableRows.filter((_, rowIndex) => rowIndex !== index));
  }

  function setColumnPreset(column_preset: ColumnPresetKey) {
    onChange({ ...block, column_preset });
  }

  function setRowLinkedIssue(index: number, linkedIssueId: string | null) {
    const next = [...tableRows];
    next[index] = { ...next[index], linked_issue_id: linkedIssueId };
    emitRows(next);
  }

  function buildRowLinkHandlers(
    row: FindingRow,
    index: number
  ): {
    onLinkIssue?: (issueId: string) => void | Promise<void>;
    onMarkNewIssue?: () => void | Promise<void>;
    onUnlinkIssue?: () => void | Promise<void>;
  } {
    if (disabled) {
      return {};
    }

    if (lineDerived && onLinkRow) {
      return {
        onLinkIssue: (issueId) => onLinkRow(row.id, issueId),
        onMarkNewIssue: () => onLinkRow(row.id, null),
        onUnlinkIssue: () => onLinkRow(row.id, null),
      };
    }

    if (!lineDerived) {
      return {
        onLinkIssue: (issueId) => {
          setRowLinkedIssue(index, issueId);
        },
        onMarkNewIssue: () => {
          setRowLinkedIssue(index, null);
        },
        onUnlinkIssue: () => {
          setRowLinkedIssue(index, null);
        },
      };
    }

    return {};
  }

  const visibleColumns = columns.filter((column) => column.id !== "photos");
  const tableColumnCount = visibleColumns.length + (tableReadOnly ? 0 : 1);

  if (lineDerived) {
    return (
      <div className="space-y-3">
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
    );
  }

  const editableRows =
    tableRows.length > 0 ? tableRows : [emptyFindingRow(0)];

  return (
    <div className="space-y-3">
      <label className="block space-y-1 text-sm">
        <span className="font-medium">preset עמודות</span>
        <select
          className={FR_TOUCH_INPUT}
          value={block.column_preset}
          disabled={tableReadOnly}
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

      <div className="overflow-x-auto">
        <table className="w-full min-w-[32rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-zinc-200 text-right">
              {visibleColumns.map((column) => (
                <th key={column.id} className="px-2 py-2 font-medium">
                  {column.header_he}
                </th>
              ))}
              {tableReadOnly ? null : <th className="w-16 px-2 py-2" />}
            </tr>
          </thead>
          <tbody>
            {editableRows.map((row, index) => {
              const linkHandlers = buildRowLinkHandlers(row, index);
              return (
              <Fragment key={row.id}>
                <tr
                  className="border-b border-zinc-100 align-top"
                >
                  {visibleColumns.map((column) => {
                    const field = FINDING_ROW_FIELDS[column.id];
                    if (!field) {
                      return (
                        <td key={column.id} className="px-2 py-2">
                          -
                        </td>
                      );
                    }

                    const value = String(row[field] ?? "");
                    const isLong = field === "description" || field === "notes";

                    return (
                      <td key={column.id} className="px-2 py-2">
                        {isLong ? (
                          <textarea
                            className={FR_TOUCH_TEXTAREA}
                            rows={2}
                            value={value}
                            disabled={tableReadOnly}
                            onChange={(event) =>
                              updateRow(index, field, event.target.value)
                            }
                          />
                        ) : (
                          <input
                            className={FR_TOUCH_INPUT}
                            value={value}
                            disabled={tableReadOnly}
                            onChange={(event) =>
                              updateRow(index, field, event.target.value)
                            }
                          />
                        )}
                      </td>
                    );
                  })}
                  {tableReadOnly ? null : (
                    <td className="px-2 py-2">
                      <Button
                        type="button"
                        variant="secondary"
                        className={FR_TOUCH_BUTTON}
                        onClick={() => removeRow(index)}
                      >
                        הסר
                      </Button>
                    </td>
                  )}
                </tr>
                <FindingRowMatchHintRow
                  row={row}
                  projectId={projectId}
                  organizationId={organizationId}
                  reportId={reportId}
                  disabled={disabled}
                  linking={linkingRowId === row.id}
                  columnCount={tableColumnCount}
                  {...linkHandlers}
                />
              </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {tableReadOnly ? null : (
        <Button
          type="button"
          variant="secondary"
          className={FR_TOUCH_BUTTON}
          onClick={addRow}
        >
          הוסף שורה לבלוק
        </Button>
      )}
    </div>
  );
}
