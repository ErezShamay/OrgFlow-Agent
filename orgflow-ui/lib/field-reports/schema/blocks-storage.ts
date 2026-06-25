/**
 * אחסון blocks[] ב-header_fields - CRUD, סנכרון legacy (FR-2.1).
 */

import {
  constructionProgressTitleHe,
  serializeConstructionProgressRows,
  type ConstructionProgressRow,
} from "../construction-progress";
import { createEmptyChecklistItem } from "./checklist-item-mutations";
import { normalizeReportBlocks } from "./normalize";
import type {
  FindingRow,
  FindingsTableBlock,
  ProgressRow,
  ProgressTableBlock,
  ReportBlock,
  ReportBlockKind,
} from "./types";

export const LEGACY_PROGRESS_BLOCK_ID = "legacy-progress-table";
export const LEGACY_FINDINGS_BLOCK_ID = "legacy-findings-table";

export type NormalizeBlocksOptions = {
  /** שורות דוח - ליצירת findings block כשאין blocks (derive read-only). */
  lines?: unknown[] | null;
};

/**
 * טוען blocks מ-header_fields - מ-blocks מפורשים או ממיר מ-legacy.
 */
export function normalizeBlocksFromHeader(
  raw: Record<string, unknown>,
  visitType: string,
  options?: NormalizeBlocksOptions
): ReportBlock[] {
  return normalizeReportBlocks(raw, visitType, options?.lines ?? null);
}

export function findProgressTableBlock(
  blocks: ReportBlock[]
): ProgressTableBlock | null {
  const match = blocks.find(
    (block): block is ProgressTableBlock => block.kind === "progress_table"
  );
  return match ?? null;
}

export function findFindingsTableBlock(
  blocks: ReportBlock[]
): FindingsTableBlock | null {
  const match = blocks.find(
    (block): block is FindingsTableBlock => block.kind === "findings_table"
  );
  return match ?? null;
}

/**
 * ממיר שורות בלוק התקדמות ל-`construction_progress`.
 * לא מסנן שורות ריקות - כדי ש«הוסף שורה» יישאר ב-UI עד מילוי (סינון רק ב-API/PDF).
 */
export function progressRowsToConstructionProgress(
  rows: ProgressRow[]
): ConstructionProgressRow[] {
  return rows.map((row) => ({
    description: row.description,
    status: row.status,
    completion_date: row.completion_date,
  }));
}

export function constructionProgressToProgressRows(
  rows: ConstructionProgressRow[]
): ProgressRow[] {
  return rows.map((row, index) => ({
    id: `progress-row-${index}`,
    description: row.description,
    status: row.status,
    completion_date: row.completion_date,
    sort_order: index,
  }));
}

/**
 * מסנכרן construction_progress מבלוק ההתקדמות (אם קיים), אחרת משאיר fallback.
 */
export function resolveConstructionProgressFromBlocks(
  blocks: ReportBlock[],
  fallback: ConstructionProgressRow[]
): ConstructionProgressRow[] {
  const progressBlock = findProgressTableBlock(blocks);
  if (!progressBlock || progressBlock.rows.length === 0) {
    return fallback;
  }
  return progressRowsToConstructionProgress(progressBlock.rows);
}

export function replaceProgressTableRows(
  blocks: ReportBlock[],
  rows: ProgressRow[],
  visitType: string
): ReportBlock[] {
  const existing = findProgressTableBlock(blocks);
  if (existing) {
    return blocks.map((block) =>
      block.kind === "progress_table" && block.id === existing.id
        ? { ...block, rows }
        : block
    );
  }

  const progressBlock: ProgressTableBlock = {
    id: LEGACY_PROGRESS_BLOCK_ID,
    kind: "progress_table",
    title_he: constructionProgressTitleHe(visitType),
    column_preset: "progress",
    rows,
    sort_order: 0,
  };

  return reindexBlockSortOrder([progressBlock, ...blocks]);
}

export function dualWriteHeaderBlocksAndProgress(
  blocks: ReportBlock[],
  construction_progress: ConstructionProgressRow[],
  visitType: string
): { blocks: ReportBlock[]; construction_progress: ConstructionProgressRow[] } {
  const usesFinishingChecklist =
    visitType === "FINISHING_APARTMENTS"
    && blocks.some(
      (block) =>
        block.kind === "checklist" || block.kind === "supervision_checklist"
    );

  if (usesFinishingChecklist) {
    return { blocks, construction_progress };
  }

  const progressRows = constructionProgressToProgressRows(construction_progress);
  const syncedBlocks = replaceProgressTableRows(blocks, progressRows, visitType);
  const syncedProgress = progressRowsToConstructionProgress(
    findProgressTableBlock(syncedBlocks)?.rows ?? progressRows
  );

  return {
    blocks: syncedBlocks,
    construction_progress: syncedProgress,
  };
}

export function serializeBlocksForApi(blocks: ReportBlock[]): unknown[] {
  return blocks.map(serializeReportBlockForApi);
}

export function addBlock(
  blocks: ReportBlock[],
  block: ReportBlock
): ReportBlock[] {
  const sort_order = blocks.length;
  return reindexBlockSortOrder([...blocks, { ...block, sort_order }]);
}

export function updateBlock(
  blocks: ReportBlock[],
  blockId: string,
  updater: (block: ReportBlock) => ReportBlock
): ReportBlock[] {
  return blocks.map((block) =>
    block.id === blockId ? updater(block) : block
  );
}

export function removeBlock(
  blocks: ReportBlock[],
  blockId: string
): ReportBlock[] {
  return reindexBlockSortOrder(blocks.filter((block) => block.id !== blockId));
}

export function reorderBlocks(
  blocks: ReportBlock[],
  fromIndex: number,
  toIndex: number
): ReportBlock[] {
  if (
    fromIndex < 0 ||
    toIndex < 0 ||
    fromIndex >= blocks.length ||
    toIndex >= blocks.length ||
    fromIndex === toIndex
  ) {
    return blocks;
  }

  const next = [...blocks];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return reindexBlockSortOrder(next);
}

/**
 * ממיר שורות דוח ל-FindingRow[] - derive read-only לבלוק ממצאים (לא כותב ל-lines).
 */
export function deriveFindingRowsFromReportLines(
  lines: unknown[] | null | undefined
): FindingRow[] {
  if (!Array.isArray(lines) || lines.length === 0) {
    return [];
  }

  const blocks = normalizeReportBlocks({}, "STRUCTURE_SITE", lines);
  const findings = findFindingsTableBlock(blocks);
  return findings?.rows ?? [];
}

export function createEmptyBlockForKind(
  kind: ReportBlockKind,
  visitType: string,
  options?: { id?: string; title_he?: string }
): ReportBlock {
  const id = options?.id ?? `block-${kind}-${Date.now()}`;
  const base = {
    id,
    title_he: options?.title_he ?? defaultTitleForBlockKind(kind, visitType),
    sort_order: 0,
  };

  switch (kind) {
    case "progress_table":
      return {
        ...base,
        kind: "progress_table",
        column_preset: "progress",
        rows: [],
      };
    case "findings_table":
      return {
        ...base,
        kind: "findings_table",
        column_preset: "rich",
        rows: [],
      };
    case "checklist":
      return {
        ...base,
        kind: "checklist",
        items: [createEmptyChecklistItem(0)],
      };
    case "supervision_checklist":
      return {
        ...base,
        kind: "supervision_checklist",
        construction_stage: "FINISHING",
        visit_scope: "APARTMENT",
        items: [],
      };
    case "free_text":
      return { ...base, kind: "free_text", body_he: "" };
    case "image":
      return { ...base, kind: "image", caption_he: null, image_url: null };
    default: {
      const _exhaustive: never = kind;
      throw new Error(`Unsupported block kind: ${_exhaustive}`);
    }
  }
}

function defaultTitleForBlockKind(
  kind: ReportBlockKind,
  visitType: string
): string {
  switch (kind) {
    case "progress_table":
      return constructionProgressTitleHe(visitType);
    case "findings_table":
      return "ממצאים / עבודות";
    case "checklist":
      return "צ'קליסט גמר";
    case "supervision_checklist":
      return "צ'קליסט מפקח";
    case "free_text":
      return "טקסט חופשי";
    case "image":
      return "הדמיית פרויקט";
    default: {
      const _exhaustive: never = kind;
      return _exhaustive;
    }
  }
}

function reindexBlockSortOrder(blocks: ReportBlock[]): ReportBlock[] {
  return blocks.map((block, index) => ({
    ...block,
    sort_order: index,
  }));
}

function serializeReportBlockForApi(block: ReportBlock): Record<string, unknown> {
  const base: Record<string, unknown> = {
    id: block.id,
    kind: block.kind,
    title_he: block.title_he,
    sort_order: block.sort_order ?? 0,
  };

  switch (block.kind) {
    case "progress_table":
      return {
        ...base,
        column_preset: block.column_preset,
        rows: block.rows.map(serializeProgressRowForApi),
      };
    case "findings_table":
      return {
        ...base,
        column_preset: block.column_preset,
        rows: block.rows.map(serializeFindingRowForApi),
      };
    case "checklist":
      return {
        ...base,
        items: block.items.map((item) => ({
          id: item.id,
          label_he: item.label_he,
          checked: item.checked,
          notes: item.notes ?? null,
          sort_order: item.sort_order ?? 0,
        })),
      };
    case "supervision_checklist":
      return {
        ...base,
        construction_stage: block.construction_stage,
        visit_scope: block.visit_scope,
        apartment_id: block.apartment_id ?? null,
        apartment_number: block.apartment_number ?? null,
        ad_hoc_apartment: block.ad_hoc_apartment ?? false,
        public_area_id: block.public_area_id ?? null,
        items: block.items.map((item) => ({
          id: item.id,
          catalog_issue_id: item.catalog_issue_id,
          issue_name_he: item.issue_name_he,
          category_id: item.category_id,
          category_name_he: item.category_name_he,
          top_family: item.top_family,
          standard_ref: item.standard_ref,
          severity: item.severity ?? null,
          status: item.status,
          notes: item.notes ?? null,
          photo_ids: item.photo_ids,
          linked_line_id: item.linked_line_id ?? null,
          sort_order: item.sort_order,
          ...(item.hidden ? { hidden: true } : {}),
          ...(item.is_custom ? { is_custom: true } : {}),
        })),
      };
    case "free_text":
      return { ...base, body_he: block.body_he };
    case "image":
      return {
        ...base,
        caption_he: block.caption_he ?? null,
        image_url: block.image_url ?? null,
        storage_path: block.storage_path ?? null,
      };
    default: {
      const _exhaustive: never = block;
      return _exhaustive;
    }
  }
}

function serializeProgressRowForApi(row: ProgressRow): Record<string, unknown> {
  return {
    id: row.id,
    description: row.description,
    status: row.status,
    completion_date: row.completion_date,
    sort_order: row.sort_order ?? 0,
  };
}

function serializeFindingRowForApi(row: FindingRow): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    id: row.id,
    location: row.location ?? null,
    trade: row.trade ?? null,
    status: row.status ?? null,
    description: row.description ?? null,
    notes: row.notes ?? null,
    sort_order: row.sort_order ?? 0,
  };

  if (row.severity) {
    payload.severity = row.severity;
  }
  if (row.standard_ref) {
    payload.standard_ref = row.standard_ref;
  }
  if (row.issue_id) {
    payload.issue_id = row.issue_id;
  }
  if (row.group_key) {
    payload.group_key = row.group_key;
  }
  if (row.group_label_he) {
    payload.group_label_he = row.group_label_he;
  }
  if (row.block_id) {
    payload.block_id = row.block_id;
  }
  if (row.has_photo) {
    payload.has_photo = true;
  }
  if (row.photo_ids?.length) {
    payload.photo_ids = row.photo_ids;
  }

  return payload;
}
