/**
 * מיגרציה ממבנה legacy (progress + ממצאים יחיד) ל-preset גמר (צ'קליסט + לובי + דירות).
 */

import { defaultReportBlocksForVisitType } from "./block-defaults";
import {
  LEGACY_FINDINGS_BLOCK_ID,
  LEGACY_PROGRESS_BLOCK_ID,
} from "./blocks-storage";
import { defaultFinishingChecklistItems } from "./checklist-presets";
import type {
  ChecklistBlock,
  ChecklistItem,
  FindingRow,
  FindingsTableBlock,
  ProgressRow,
  ReportBlock,
} from "./types";

const LOBBY_GROUP_PREFIXES = ["floor:", "area:"] as const;

const LOBBY_PROGRESS_PATTERN =
  /מדרגות|לובי|מעברים|חדר מדרגות/i;

const PROGRESS_TO_CHECKLIST_ITEM_ID: readonly {
  pattern: RegExp;
  itemId: string;
}[] = [
  { pattern: /בעלים|גמר בדירות/i, itemId: "owners" },
  { pattern: /חללים/i, itemId: "spaces" },
  { pattern: /חשמל/i, itemId: "electrical" },
  { pattern: /אינסטלציה/i, itemId: "plumbing" },
  { pattern: /איטום.*רטוב|רטובים/i, itemId: "wet_rooms_sealing" },
  { pattern: /מרפסות/i, itemId: "balcony_sealing" },
];

export function hasModernFinishingBlockLayout(
  blocks: readonly ReportBlock[]
): boolean {
  return blocks.some(
    (block) =>
      block.kind === "checklist" || block.kind === "supervision_checklist"
  );
}

export function shouldMigrateLegacyFinishingBlocks(
  visitType: string,
  raw: Record<string, unknown>,
  blocks: readonly ReportBlock[],
  reportLines?: unknown[] | null
): boolean {
  if (visitType !== "FINISHING_APARTMENTS") {
    return false;
  }

  if (hasModernFinishingBlockLayout(blocks)) {
    return false;
  }

  return (
    hasLegacyFinishingProgressData(raw, blocks)
    || hasLegacyFinishingLines(reportLines)
    || isLegacyOnlyFinishingBlocks(blocks)
  );
}

export function migrateLegacyFinishingBlocks(
  raw: Record<string, unknown>,
  reportLines?: unknown[] | null,
  existingBlocks: readonly ReportBlock[] = []
): ReportBlock[] {
  const blocks = defaultReportBlocksForVisitType("FINISHING_APARTMENTS");
  const checklist = blocks.find(
    (block): block is ChecklistBlock => block.kind === "checklist"
  );
  const lobbyBlock = blocks.find(
    (block): block is FindingsTableBlock =>
      block.kind === "findings_table"
      && block.id === "default-lobby-findings"
  );
  const apartmentBlock = blocks.find(
    (block): block is FindingsTableBlock =>
      block.kind === "findings_table"
      && block.id === "default-apartment-findings"
  );

  if (!checklist || !lobbyBlock || !apartmentBlock) {
    return [...blocks];
  }

  const progressRows = collectProgressRows(raw, existingBlocks);
  const findingRows = collectFindingRows(raw, reportLines, existingBlocks);

  checklist.items = migrateChecklistItems(checklist.items, progressRows);

  const lobbyRows: FindingRow[] = [];
  const apartmentRows: FindingRow[] = [];

  for (const row of progressRows) {
    const lobbyFinding = lobbyFindingFromProgressRow(row);
    if (lobbyFinding) {
      lobbyRows.push(lobbyFinding);
    }
  }

  for (const row of findingRows) {
    if (row.block_id === lobbyBlock.id || isLobbyFindingRow(row)) {
      lobbyRows.push({ ...row, block_id: lobbyBlock.id });
      continue;
    }

    apartmentRows.push({
      ...row,
      block_id: row.block_id || apartmentBlock.id,
    });
  }

  lobbyBlock.rows = lobbyRows;
  apartmentBlock.rows = apartmentRows;

  return blocks;
}

function hasLegacyFinishingProgressData(
  raw: Record<string, unknown>,
  blocks: readonly ReportBlock[]
): boolean {
  if (collectProgressRows(raw, blocks).length > 0) {
    return true;
  }

  return blocks.some(
    (block) =>
      block.kind === "progress_table"
      && (block.id === LEGACY_PROGRESS_BLOCK_ID
        || block.title_he === "התקדמות הבנייה")
  );
}

function hasLegacyFinishingLines(reportLines?: unknown[] | null): boolean {
  return Array.isArray(reportLines) && reportLines.length > 0;
}

function isLegacyOnlyFinishingBlocks(blocks: readonly ReportBlock[]): boolean {
  if (blocks.length === 0) {
    return false;
  }

  return blocks.every(
    (block) =>
      block.id === LEGACY_PROGRESS_BLOCK_ID
      || block.id === LEGACY_FINDINGS_BLOCK_ID
      || block.kind === "progress_table"
      || (block.kind === "findings_table"
        && block.title_he === "ממצאים / עבודות")
  );
}

function collectProgressRows(
  raw: Record<string, unknown>,
  blocks: readonly ReportBlock[]
): ProgressRow[] {
  const fromBlock = blocks
    .filter((block): block is Extract<ReportBlock, { kind: "progress_table" }> =>
      block.kind === "progress_table"
    )
    .flatMap((block) => block.rows);

  if (fromBlock.length > 0) {
    return fromBlock;
  }

  if (!Array.isArray(raw.construction_progress)) {
    return [];
  }

  return raw.construction_progress.flatMap((item, index): ProgressRow[] => {
    if (!item || typeof item !== "object") {
      return [];
    }
    const row = item as Record<string, unknown>;
    const progressRow: ProgressRow = {
      id: `legacy-progress-${index}`,
      description: String(row.description ?? "").trim(),
      status: String(row.status ?? "").trim(),
      completion_date: String(row.completion_date ?? "").trim(),
      sort_order: index,
    };
    if (
      !progressRow.description
      && !progressRow.status
      && !progressRow.completion_date
    ) {
      return [];
    }
    return [progressRow];
  });
}

function collectFindingRows(
  raw: Record<string, unknown>,
  reportLines: unknown[] | null | undefined,
  blocks: readonly ReportBlock[]
): FindingRow[] {
  const fromLines = Array.isArray(reportLines)
    ? reportLines
        .map((line, index) => findingRowFromLine(line, index))
        .filter((row): row is FindingRow => row !== null)
    : [];

  if (fromLines.length > 0) {
    return fromLines;
  }

  const findingsBlock = blocks.find(
    (block): block is FindingsTableBlock => block.kind === "findings_table"
  );

  return findingsBlock?.rows ?? [];
}

function migrateChecklistItems(
  items: ChecklistItem[],
  progressRows: ProgressRow[]
): ChecklistItem[] {
  const updates = new Map<string, { checked: boolean; notes: string | null }>();

  for (const row of progressRows) {
    const description = row.description.trim();
    if (!description || LOBBY_PROGRESS_PATTERN.test(description)) {
      continue;
    }

    const mapping = PROGRESS_TO_CHECKLIST_ITEM_ID.find((entry) =>
      entry.pattern.test(description)
    );
    if (!mapping) {
      continue;
    }

    const status = row.status.trim();
    const completion = row.completion_date.trim();
    const checked = isProgressDone(status, completion);
    const notes = buildChecklistNotes(status, completion, checked);

    updates.set(mapping.itemId, { checked, notes });
  }

  if (updates.size === 0) {
    return items.length > 0 ? items : defaultFinishingChecklistItems();
  }

  return (items.length > 0 ? items : defaultFinishingChecklistItems()).map(
    (item) => {
      const defId = item.id.replace(/^checklist-/, "");
      const update = updates.get(defId);
      if (!update) {
        return item;
      }

      return {
        ...item,
        checked: update.checked,
        notes: update.notes,
      };
    }
  );
}

function lobbyFindingFromProgressRow(row: ProgressRow): FindingRow | null {
  const description = row.description.trim();
  if (!description || !LOBBY_PROGRESS_PATTERN.test(description)) {
    return null;
  }

  const status = row.status.trim();
  const completion = row.completion_date.trim();
  if (!status && !completion) {
    return null;
  }

  return {
    id: `migrated-lobby-${row.id}`,
    location: description,
    trade: null,
    status: status || null,
    description: completion ? `תאריך: ${completion}` : null,
    notes: null,
    sort_order: row.sort_order ?? 0,
    block_id: "default-lobby-findings",
  };
}

function isLobbyFindingRow(row: FindingRow): boolean {
  const groupKey = row.group_key?.trim();
  if (!groupKey) {
    return false;
  }

  return LOBBY_GROUP_PREFIXES.some((prefix) => groupKey.startsWith(prefix));
}

function isProgressDone(status: string, completion: string): boolean {
  if (completion) {
    return true;
  }

  return /בוצע|הושלם|תקין|סיום/i.test(status);
}

function findingRowFromLine(
  value: unknown,
  index: number
): FindingRow | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;
  const pickString = (key: string): string | null => {
    const text = raw[key];
    if (typeof text !== "string") {
      return null;
    }
    const trimmed = text.trim();
    return trimmed || null;
  };

  return {
    id:
      typeof raw.id === "string" && raw.id.trim()
        ? raw.id.trim()
        : `line-${index}`,
    location: pickString("location"),
    trade: pickString("trade"),
    status: pickString("status"),
    description: pickString("description"),
    notes: pickString("notes"),
    severity: pickString("severity"),
    standard_ref: pickString("standard_ref"),
    issue_id: pickString("issue_id"),
    group_key: pickString("group_key"),
    group_label_he: pickString("group_label_he"),
    block_id: pickString("block_id"),
    sort_order:
      typeof raw.sort_order === "number" ? raw.sort_order : index,
    has_photo: raw.has_photo === true,
    photo_ids: Array.isArray(raw.photo_ids)
      ? raw.photo_ids.map((id) => String(id).trim()).filter(Boolean)
      : undefined,
  };
}

function buildChecklistNotes(
  status: string,
  completion: string,
  checked: boolean
): string | null {
  const parts = [status, completion ? `תאריך: ${completion}` : ""]
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length === 0) {
    return null;
  }

  if (checked && parts.length === 1 && isProgressDone(parts[0], "")) {
    return null;
  }

  return parts.join(" · ");
}
