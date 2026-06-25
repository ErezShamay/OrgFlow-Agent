/**
 * הזרקה וסנכרון של בלוקי טקסט קבוע (boilerplate) - FR-4.2.
 */

import { defaultFixedTextBlocks } from "./block-defaults";
import type { FixedTextBlock, FixedTextBlockKind } from "./types";

/** יוצר סעיף טקסט מותאם ריק לדוח. */
export function createEmptyCustomFixedTextBlock(
  sortOrder: number
): FixedTextBlock {
  return {
    id: `fixed-text-custom-${Date.now()}`,
    kind: "custom",
    title_he: "",
    body_he: "",
    enabled: true,
    sort_order: sortOrder,
  };
}

/** מזהה סוגי בלוק שאינם ניתנים למחיקה (רק כיבוי). */
export const NON_REMOVABLE_FIXED_TEXT_KINDS = new Set<FixedTextBlockKind>([
  "non_conformance_disclaimer",
  "safety_disclaimer",
  "winter_recommendations",
  "agreement_notes",
]);

export function isRemovableFixedTextBlock(block: FixedTextBlock): boolean {
  return block.kind === "custom";
}

/** כותרות ברירת מחדל לסוגי בלוק (לעריכה ב-UI). */
export const FIXED_TEXT_BLOCK_KIND_LABELS: Record<FixedTextBlockKind, string> = {
  non_conformance_disclaimer: "הסתייגות אי-התאמה",
  safety_disclaimer: "אחריות בטיחות",
  winter_recommendations: "המלצות חורף / עונת גשמים",
  agreement_notes: "הערות הסכם / לקבלן",
  custom: "טקסט מותאם",
};

/** חודשי עונת גשמים - אוקטובר עד מרץ (כולל). */
const WINTER_SEASON_MONTHS = new Set([10, 11, 12, 1, 2, 3]);

export function isWinterSeasonDate(value: Date | string): boolean {
  const date = typeof value === "string" ? parseVisitDate(value) : value;
  if (!date || Number.isNaN(date.getTime())) {
    return false;
  }
  return WINTER_SEASON_MONTHS.has(date.getMonth() + 1);
}

/**
 * בלוקי boilerplate לדוח חדש - disclaimers מופעלים; חורף לפי תאריך ביקור.
 */
export function buildFixedTextBlocksForNewReport(options?: {
  visitDate?: string;
  includeBoilerplate?: boolean;
}): FixedTextBlock[] {
  if (options?.includeBoilerplate === false) {
    return [];
  }

  const blocks = defaultFixedTextBlocks().map((block) => ({ ...block }));
  if (options?.visitDate) {
    return applyWinterSeasonToBlocks(blocks, options.visitDate);
  }
  return blocks;
}

/** מפעיל/מכבה בלוק המלצות חורף לפי תאריך הביקור. */
export function applyWinterSeasonToBlocks(
  blocks: FixedTextBlock[],
  visitDate: Date | string
): FixedTextBlock[] {
  const enableWinter = isWinterSeasonDate(visitDate);
  return blocks.map((block) =>
    block.kind === "winter_recommendations"
      ? { ...block, enabled: enableWinter }
      : block
  );
}

export function resolveIncludeFixedTextBlocks(
  raw: Record<string, unknown>,
  blocks: FixedTextBlock[]
): boolean {
  if (typeof raw.include_fixed_text_blocks === "boolean") {
    return raw.include_fixed_text_blocks;
  }
  return blocks.length > 0;
}

/**
 * טוען בלוקים מ-header_fields או בונה מ-legacy - ללא הזרקה אוטומטית בטעינה.
 */
export function resolveFixedTextBlocksFromHeader(
  raw: Record<string, unknown>,
  visitDate?: string
): FixedTextBlock[] {
  if (Array.isArray(raw.fixed_text_blocks) && raw.fixed_text_blocks.length > 0) {
    return normalizeFixedTextBlocksList(raw.fixed_text_blocks);
  }

  const fromLegacy = fixedTextBlocksFromLegacyHeader(raw);
  if (fromLegacy.length > 0) {
    return visitDate ? applyWinterSeasonToBlocks(fromLegacy, visitDate) : fromLegacy;
  }

  return [];
}

/** מסנכרן שדות legacy ל-PDF ו-API ישן מתוך בלוקים מופעלים. */
export function syncLegacyFieldsFromFixedTextBlocks(
  blocks: FixedTextBlock[],
  current: {
    winter_recommendations: string;
    contractor_notes: string[];
    project_updates: string[];
  },
  includeFixedText: boolean
): {
  winter_recommendations: string;
  contractor_notes: string[];
  project_updates: string[];
} {
  if (!includeFixedText) {
    return current;
  }

  let winter_recommendations = current.winter_recommendations;
  let contractor_notes = [...current.contractor_notes];
  let project_updates = [...current.project_updates];

  const winterBlock = blocks.find(
    (block) => block.kind === "winter_recommendations"
  );
  if (winterBlock) {
    winter_recommendations = winterBlock.enabled ? winterBlock.body_he : "";
  }

  for (const block of blocks) {
    if (!block.enabled) {
      continue;
    }

    switch (block.kind) {
      case "winter_recommendations":
        break;
      case "agreement_notes": {
        const lines = block.body_he
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean);
        if (lines.length) {
          contractor_notes = lines;
        }
        break;
      }
      case "custom":
        if (block.title_he?.includes("עדכונים")) {
          const lines = block.body_he
            .split("\n")
            .map((line) => line.trim())
            .filter(Boolean);
          if (lines.length) {
            project_updates = lines;
          }
        }
        break;
      default:
        break;
    }
  }

  return { winter_recommendations, contractor_notes, project_updates };
}

function fixedTextBlocksFromLegacyHeader(
  raw: Record<string, unknown>
): FixedTextBlock[] {
  const blocks: FixedTextBlock[] = [];
  let sortOrder = 0;

  const winterText =
    typeof raw.winter_recommendations === "string"
      ? raw.winter_recommendations.trim()
      : "";
  if (winterText) {
    blocks.push({
      id: "legacy-winter-recommendations",
      kind: "winter_recommendations",
      title_he: FIXED_TEXT_BLOCK_KIND_LABELS.winter_recommendations,
      body_he: winterText,
      enabled: true,
      sort_order: sortOrder++,
    });
  }

  if (Array.isArray(raw.contractor_notes)) {
    const notes = raw.contractor_notes
      .map((item) => String(item).trim())
      .filter(Boolean);
    if (notes.length) {
      blocks.push({
        id: "legacy-contractor-notes",
        kind: "agreement_notes",
        title_he: FIXED_TEXT_BLOCK_KIND_LABELS.agreement_notes,
        body_he: notes.join("\n"),
        enabled: true,
        sort_order: sortOrder++,
      });
    }
  }

  return blocks;
}

function normalizeFixedTextBlocksList(value: unknown): FixedTextBlock[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const blocks: FixedTextBlock[] = [];
  for (let index = 0; index < value.length; index += 1) {
    const item = value[index];
    if (!item || typeof item !== "object") {
      continue;
    }
    const raw = item as Record<string, unknown>;
    const kind = raw.kind;
    if (typeof kind !== "string" || !isFixedTextBlockKind(kind)) {
      continue;
    }
    const bodyHe = typeof raw.body_he === "string" ? raw.body_he.trim() : "";
    if (!bodyHe && kind !== "custom") {
      continue;
    }

    blocks.push({
      id:
        typeof raw.id === "string" && raw.id.trim()
          ? raw.id.trim()
          : `fixed-text-${index}`,
      kind,
      title_he:
        typeof raw.title_he === "string" && raw.title_he.trim()
          ? raw.title_he.trim()
          : defaultTitleForKind(kind),
      body_he: bodyHe,
      enabled: raw.enabled !== false,
      sort_order:
        typeof raw.sort_order === "number" ? raw.sort_order : index,
    });
  }

  return blocks.sort(
    (left, right) => (left.sort_order ?? 0) - (right.sort_order ?? 0)
  );
}

function defaultTitleForKind(kind: FixedTextBlockKind): string | null {
  if (kind === "non_conformance_disclaimer" || kind === "safety_disclaimer") {
    return null;
  }
  return FIXED_TEXT_BLOCK_KIND_LABELS[kind];
}

function isFixedTextBlockKind(value: string): value is FixedTextBlockKind {
  return (
    value === "safety_disclaimer"
    || value === "non_conformance_disclaimer"
    || value === "winter_recommendations"
    || value === "agreement_notes"
    || value === "custom"
  );
}

function parseVisitDate(value: string): Date | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const iso = trimmed.length === 10 ? `${trimmed}T12:00:00` : trimmed;
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? null : date;
}
