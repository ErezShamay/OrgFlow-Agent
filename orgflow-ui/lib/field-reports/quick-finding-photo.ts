import { createClientLineUuid } from "@/lib/field-reports/ids";
import {
  buildGroupLabelHe,
  defaultLineGroupSelection,
  lineGroupFieldsFromSelection,
  type LineGroupSelection,
} from "@/lib/field-reports/line-grouping";
import type { UpsertLineInput } from "@/lib/field-reports/repositories/reports-repository";

export const QUICK_FINDING_PHOTO_DESCRIPTION = "ממצא מתמונה";

/** מספר לחיצות מינימלי: כפתור צילום → לחיצת shutter / בחירת תמונה. */
export const QUICK_FINDING_PHOTO_TAP_COUNT = 2;

export function formatQuickFindingDescription(sequence = 1): string {
  if (sequence <= 1) {
    return QUICK_FINDING_PHOTO_DESCRIPTION;
  }

  return `${QUICK_FINDING_PHOTO_DESCRIPTION} ${sequence}`;
}

export function buildQuickFindingLocationFromGroup(
  group: LineGroupSelection = defaultLineGroupSelection()
): string | null {
  return buildGroupLabelHe(group);
}

export function buildQuickFindingLinePayload(options: {
  lineId?: string;
  group?: LineGroupSelection;
  sequence?: number;
}): UpsertLineInput & { client_line_uuid: string } {
  const lineId = options.lineId ?? createClientLineUuid();
  const group = options.group ?? defaultLineGroupSelection();

  return {
    client_line_uuid: lineId,
    description: formatQuickFindingDescription(options.sequence ?? 1),
    location: buildQuickFindingLocationFromGroup(group),
    ...lineGroupFieldsFromSelection(group),
  };
}
