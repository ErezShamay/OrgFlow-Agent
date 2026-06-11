import {
  DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE,
  DEFAULT_SAFETY_DISCLAIMER_HE,
} from "../schema/block-defaults";
import {
  resolveFixedTextBlocksFromHeader,
} from "../schema/fixed-text-inject";
import type { FixedTextBlockKind } from "../schema/types";
import { resolveStringList } from "./render-header";

const COVER_NUMBERED_KINDS: FixedTextBlockKind[] = [
  "non_conformance_disclaimer",
  "safety_disclaimer",
];

/** סעיפים שמופיעים בעמוד השער כרשימה ממוספרת - לא בסוף הדוח. */
export function isCoverNumberedFixedTextKind(
  kind: FixedTextBlockKind
): boolean {
  return COVER_NUMBERED_KINDS.includes(kind);
}

/**
 * רשימה ממוספרת בעמוד הראשון: עדכוני פרויקט ואז הצהרות (כמו דוחות example_reports).
 */
export function buildCoverNumberedEntries(
  headerFields: Record<string, unknown>,
  visitDate?: string
): string[] {
  const entries: string[] = [];
  const projectUpdates = resolveStringList(headerFields.project_updates);
  entries.push(...projectUpdates);

  const blocks = resolveFixedTextBlocksFromHeader(
    headerFields,
    visitDate
  ).filter((block) => block.enabled);
  const includeBoilerplate =
    headerFields.include_fixed_text_blocks !== false;

  for (const kind of COVER_NUMBERED_KINDS) {
    const block = blocks.find((entry) => entry.kind === kind);
    if (block?.body_he?.trim()) {
      entries.push(block.body_he.trim());
      continue;
    }

    if (includeBoilerplate) {
      if (kind === "non_conformance_disclaimer") {
        entries.push(DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE);
      }
      if (kind === "safety_disclaimer") {
        entries.push(DEFAULT_SAFETY_DISCLAIMER_HE);
      }
    }
  }

  return entries.filter(Boolean);
}

/** בלוקי טקסט קבוע לסוף הדוח בלבד (חורף, הערות הסכם, מותאם). */
export function resolveEndMatterFixedTextBlocks(
  headerFields: Record<string, unknown>,
  visitDate?: string
) {
  return resolveFixedTextBlocksFromHeader(headerFields, visitDate).filter(
    (block) =>
      block.enabled && !isCoverNumberedFixedTextKind(block.kind)
  );
}
