"use client";

import { type ReactNode, useMemo, useState } from "react";

import ReportChecklistBlockEditor from "@/components/field-reports/ReportChecklistBlockEditor";
import ReportFindingsBlockEditor from "@/components/field-reports/ReportFindingsBlockEditor";
import ReportProgressBlockEditor from "@/components/field-reports/ReportProgressBlockEditor";
import SupervisionChecklistEditor from "@/components/field-reports/SupervisionChecklistEditor";
import Button from "@/components/ui/Button";
import {
  ADDABLE_BLOCK_KINDS,
  REPORT_BLOCK_KIND_LABELS,
} from "@/lib/field-reports/block-kind-labels";
import { defaultReportBlocksForVisitType } from "@/lib/field-reports/schema/block-defaults";
import {
  LEGACY_FINDINGS_BLOCK_ID,
  addBlock,
  createEmptyBlockForKind,
  removeBlock,
  reorderBlocks,
  updateBlock,
} from "@/lib/field-reports/schema/blocks-storage";
import type {
  FindingsTableBlock,
  FreeTextBlock,
  ImageBlock,
  InspectMode,
  ProgressTableBlock,
  ReportBlock,
  ReportBlockKind,
  SupervisionChecklistBlock,
} from "@/lib/field-reports/schema/types";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
  FR_TOUCH_SELECT,
  FR_TOUCH_TEXTAREA,
} from "@/lib/field-reports/touch-input-class";

type ReportBlocksManagerProps = {
  blocks: ReportBlock[];
  visitType: string;
  disabled: boolean;
  projectId?: string | null;
  organizationId?: string | null;
  reportId?: string | null;
  inspectMode?: InspectMode;
  linkingRowId?: string | null;
  onLinkFindingRow?: (
    rowId: string,
    linkedIssueId: string | null
  ) => void | Promise<void>;
  /** האם blocks[] נשמר במפורש ב-header_fields (לא רק derive). */
  hasExplicitBlocks: boolean;
  /** שורות ממצאים + תמונות — מוזרק לפני טבלת הממצאים הראשונה (REQ-UX-001). */
  findingsLinesPanel?: ReactNode;
  onChange: (blocks: ReportBlock[]) => void;
};

function blockKindLabel(kind: ReportBlockKind): string {
  return REPORT_BLOCK_KIND_LABELS[kind];
}

export default function ReportBlocksManager({
  blocks,
  visitType,
  disabled,
  projectId = null,
  organizationId = null,
  reportId = null,
  inspectMode = "standard",
  linkingRowId = null,
  onLinkFindingRow,
  hasExplicitBlocks,
  findingsLinesPanel = null,
  onChange,
}: ReportBlocksManagerProps) {
  const [addKind, setAddKind] = useState<ReportBlockKind>("progress_table");

  const sortedBlocks = useMemo(
    () =>
      [...blocks].sort(
        (left, right) => (left.sort_order ?? 0) - (right.sort_order ?? 0)
      ),
    [blocks]
  );

  function patchBlock(blockId: string, updater: (block: ReportBlock) => ReportBlock) {
    onChange(updateBlock(blocks, blockId, updater));
  }

  function moveBlock(sortedIndex: number, direction: -1 | 1) {
    const targetSortedIndex = sortedIndex + direction;
    if (targetSortedIndex < 0 || targetSortedIndex >= sortedBlocks.length) {
      return;
    }

    const fromIndex = blocks.findIndex(
      (block) => block.id === sortedBlocks[sortedIndex].id
    );
    const toIndex = blocks.findIndex(
      (block) => block.id === sortedBlocks[targetSortedIndex].id
    );

    if (fromIndex < 0 || toIndex < 0) {
      return;
    }

    onChange(reorderBlocks(blocks, fromIndex, toIndex));
  }

  function handleAddBlock() {
    const block = createEmptyBlockForKind(addKind, visitType);
    onChange(addBlock(blocks, block));
  }

  function handleApplyVisitPreset() {
    onChange(defaultReportBlocksForVisitType(visitType));
  }

  function handleRemoveBlock(blockId: string) {
    onChange(removeBlock(blocks, blockId));
  }

  function isFindingsLineDerived(block: FindingsTableBlock): boolean {
    return block.id === LEGACY_FINDINGS_BLOCK_ID && !hasExplicitBlocks;
  }

  const findingsTableBlocks = useMemo(
    () =>
      sortedBlocks.filter(
        (block): block is FindingsTableBlock => block.kind === "findings_table"
      ),
    [sortedBlocks]
  );

  const hasFindingsArea =
    Boolean(findingsLinesPanel) || findingsTableBlocks.length > 0;

  function renderBlockCard(block: ReportBlock, index: number) {
    return (
      <div className="space-y-3 rounded-lg border border-zinc-100 bg-zinc-50/50 p-4 dark:border-zinc-800 dark:bg-zinc-900/30">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-sm font-medium text-zinc-600">
            {blockKindLabel(block.kind)}
          </span>
          {disabled ? null : (
            <div className="flex flex-wrap gap-1">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className={FR_TOUCH_BUTTON}
                disabled={index === 0}
                onClick={() => moveBlock(index, -1)}
                aria-label="הזז למעלה"
              >
                ↑
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className={FR_TOUCH_BUTTON}
                disabled={index === sortedBlocks.length - 1}
                onClick={() => moveBlock(index, 1)}
                aria-label="הזז למטה"
              >
                ↓
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className={FR_TOUCH_BUTTON}
                onClick={() => handleRemoveBlock(block.id)}
              >
                הסר סעיף
              </Button>
            </div>
          )}
        </div>

        <label className="block space-y-1 text-sm">
          <span className="font-medium">כותרת הסעיף</span>
          <input
            className={FR_TOUCH_INPUT}
            value={block.title_he}
            disabled={disabled}
            onChange={(event) =>
              patchBlock(block.id, (current) => ({
                ...current,
                title_he: event.target.value,
              }))
            }
          />
        </label>

        {block.kind === "progress_table" ? (
          <ReportProgressBlockEditor
            block={block as ProgressTableBlock}
            visitType={visitType}
            disabled={disabled}
            onChange={(next) => patchBlock(block.id, () => next)}
          />
        ) : null}

        {block.kind === "findings_table" ? (
          <ReportFindingsBlockEditor
            block={block as FindingsTableBlock}
            disabled={disabled}
            projectId={projectId}
            organizationId={organizationId}
            reportId={reportId}
            linkingRowId={linkingRowId}
            onLinkRow={onLinkFindingRow}
            lineDerived={isFindingsLineDerived(block as FindingsTableBlock)}
            onChange={(next) => patchBlock(block.id, () => next)}
          />
        ) : null}

        {block.kind === "free_text" ? (
          <label className="block space-y-1 text-sm">
            <span className="font-medium">תוכן</span>
            <textarea
              className={FR_TOUCH_TEXTAREA}
              rows={4}
              value={(block as FreeTextBlock).body_he}
              disabled={disabled}
              onChange={(event) =>
                patchBlock(block.id, (current) =>
                  current.kind === "free_text"
                    ? { ...current, body_he: event.target.value }
                    : current
                )
              }
            />
          </label>
        ) : null}

        {block.kind === "checklist" ? (
          <ReportChecklistBlockEditor
            block={block}
            disabled={disabled}
            onChange={(next) => patchBlock(block.id, () => next)}
          />
        ) : null}

        {block.kind === "supervision_checklist" && reportId ? (
          <SupervisionChecklistEditor
            block={block as SupervisionChecklistBlock}
            reportId={reportId}
            inspectMode={inspectMode}
            disabled={disabled}
            onChange={(next) => patchBlock(block.id, () => next)}
          />
        ) : null}

        {block.kind === "image" ? (
          <label className="block space-y-1 text-sm">
            <span className="font-medium">כיתוב תמונה</span>
            <input
              className={FR_TOUCH_INPUT}
              value={(block as ImageBlock).caption_he ?? ""}
              disabled={disabled}
              onChange={(event) =>
                patchBlock(block.id, (current) =>
                  current.kind === "image"
                    ? {
                        ...current,
                        caption_he: event.target.value || null,
                      }
                    : current
                )
              }
            />
            <p className="text-xs text-zinc-500">
              העלאת תמונה לבלוק - בשלב עתידי (FR-2.3 / PDF).
            </p>
          </label>
        ) : null}
      </div>
    );
  }

  function renderFindingsUnifiedArea() {
    if (!hasFindingsArea) {
      return null;
    }

    return (
      <div
        className="space-y-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-950/20"
        id="field-report-findings"
      >
        <div>
          <h3 className="text-lg font-semibold">ממצאים</h3>
          <p className="mt-1 text-sm text-zinc-500">
            הוסף ממצאים, צרף תמונות וערוך טבלאות — הכל נשמר בדוח ובייצוא PDF.
          </p>
        </div>
        {findingsLinesPanel}
        {findingsTableBlocks.map((block) => {
          const sortedIndex = sortedBlocks.findIndex(
            (candidate) => candidate.id === block.id
          );
          return (
            <div key={block.id}>{renderBlockCard(block, sortedIndex)}</div>
          );
        })}
      </div>
    );
  }

  function buildBlockListItems(): ReactNode[] {
    const items: ReactNode[] = [];
    let findingsUnifiedRendered = false;

    sortedBlocks.forEach((block, index) => {
      if (block.kind === "findings_table") {
        if (!findingsUnifiedRendered) {
          findingsUnifiedRendered = true;
          items.push(
            <li key="field-report-findings-unified">
              {renderFindingsUnifiedArea()}
            </li>
          );
        }
        return;
      }

      items.push(<li key={block.id}>{renderBlockCard(block, index)}</li>);
    });

    if (!findingsUnifiedRendered && hasFindingsArea) {
      items.push(
        <li key="field-report-findings-unified">
          {renderFindingsUnifiedArea()}
        </li>
      );
    }

    return items;
  }

  return (
    <section className="space-y-4 rounded-xl border border-zinc-200 p-4 md:p-5">
      <div>
        <h2 className="text-lg font-semibold">סעיפי גוף הדוח</h2>
        <p className="mt-1 text-sm text-zinc-500">
          הוסף וסדר סעיפים (התקדמות, ממצאים, טקסט). שינויים נשמרים בדוח וב-PDF.
        </p>
      </div>

      {sortedBlocks.length === 0 && !hasFindingsArea ? (
        <p className="text-sm text-zinc-500">
          אין סעיפים - הוסף סעיף או טען תבנית לפי סוג הביקור.
        </p>
      ) : (
        <ul className="space-y-4">{buildBlockListItems()}</ul>
      )}

      {disabled ? null : (
        <div className="flex flex-col gap-3 border-t border-zinc-200 pt-4 sm:flex-row sm:flex-wrap sm:items-end">
          <label className="block min-w-[12rem] flex-1 space-y-1 text-sm">
            <span className="font-medium">הוסף סעיף</span>
            <select
              className={FR_TOUCH_SELECT}
              value={addKind}
              onChange={(event) =>
                setAddKind(event.target.value as ReportBlockKind)
              }
            >
              {ADDABLE_BLOCK_KINDS.map((kind) => (
                <option key={kind} value={kind}>
                  {blockKindLabel(kind)}
                </option>
              ))}
            </select>
          </label>
          <Button
            type="button"
            variant="secondary"
            size="lg"
            className={FR_TOUCH_BUTTON}
            onClick={handleAddBlock}
          >
            + הוסף סעיף
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="lg"
            className={FR_TOUCH_BUTTON}
            onClick={handleApplyVisitPreset}
          >
            טען תבנית לסוג ביקור
          </Button>
        </div>
      )}
    </section>
  );
}
