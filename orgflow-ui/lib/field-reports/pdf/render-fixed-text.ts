import type { Content } from "pdfmake/interfaces";

import { pdfText } from "./pdf-styles";
import { isCoverNumberedFixedTextKind } from "./render-header-boilerplate";
import {
  FIXED_TEXT_BLOCK_KIND_LABELS,
  resolveFixedTextBlocksFromHeader,
} from "../schema/fixed-text-inject";
import type { FixedTextBlock } from "../schema/types";

export function hasStructuredFixedTextInHeader(
  headerFields: Record<string, unknown>
): boolean {
  return (
    Array.isArray(headerFields.fixed_text_blocks)
    && headerFields.fixed_text_blocks.length > 0
  );
}

export function shouldIncludeFixedTextInPdf(
  headerFields: Record<string, unknown>
): boolean {
  if (!hasStructuredFixedTextInHeader(headerFields)) {
    return false;
  }
  return headerFields.include_fixed_text_blocks !== false;
}

/** מציג המלצות חורף בפורמט legacy - רק כשאין fixed_text_blocks מובנים. */
export function shouldRenderLegacyWinterSection(
  headerFields: Record<string, unknown>
): boolean {
  return !hasStructuredFixedTextInHeader(headerFields);
}

export function shouldRenderLegacyContractorNotes(
  headerFields: Record<string, unknown>
): boolean {
  if (!hasStructuredFixedTextInHeader(headerFields)) {
    return true;
  }
  if (!shouldIncludeFixedTextInPdf(headerFields)) {
    return true;
  }

  const blocks = resolveFixedTextBlocksFromHeader(headerFields);
  return !blocks.some(
    (block) => block.kind === "agreement_notes" && block.enabled
  );
}

export function renderFixedTextBlocksFromHeader(
  headerFields: Record<string, unknown>,
  visitDate?: string
): Content[] {
  if (!shouldIncludeFixedTextInPdf(headerFields)) {
    return [];
  }

  const blocks = resolveFixedTextBlocksFromHeader(headerFields, visitDate).filter(
    (block) => block.enabled && !isCoverNumberedFixedTextKind(block.kind)
  );
  if (!blocks.length) {
    return [];
  }

  const content: Content[] = [];

  for (const block of blocks) {
    content.push(...renderSingleFixedTextBlock(block));
  }

  return content;
}

function renderSingleFixedTextBlock(block: FixedTextBlock): Content[] {
  const content: Content[] = [];
  const title =
    block.title_he?.trim()
    || FIXED_TEXT_BLOCK_KIND_LABELS[block.kind];

  if (
    title
    && block.kind !== "non_conformance_disclaimer"
    && block.kind !== "safety_disclaimer"
  ) {
    content.push(
      pdfText(title, {
        style: "sectionTitle",
        margin: [0, 12, 0, 6],
      })
    );
  }

  content.push(
    pdfText(block.body_he, { margin: [0, 0, 0, 12] })
  );

  return content;
}
