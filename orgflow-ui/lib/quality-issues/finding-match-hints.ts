import type { FindingMatchInput } from "@/lib/quality-issues/types";

export const FINDING_MATCH_DEBOUNCE_MS = 400;

export type FindingRowMatchFields = {
  location?: string | null;
  trade?: string | null;
  group_key?: string | null;
  issue_id?: string | null;
};

export function hasMatchableFindingFields(
  fields: FindingRowMatchFields
): boolean {
  return [fields.location, fields.trade, fields.group_key].some(
    (value) => Boolean(value?.trim())
  );
}

export function buildSuggestMatchesRequestFromFindingRow(
  fields: FindingRowMatchFields
): FindingMatchInput {
  return {
    location: fields.location?.trim() || null,
    trade: fields.trade?.trim() || null,
    group_key: fields.group_key?.trim() || null,
    catalog_issue_id: fields.issue_id?.trim() || null,
  };
}

export function formatSimilarIssueSummary(parts: {
  title: string;
  location?: string | null;
  trade?: string | null;
}): string {
  const locationTrade = [parts.location?.trim(), parts.trade?.trim()]
    .filter(Boolean)
    .join(" · ");

  return [parts.title, locationTrade].filter(Boolean).join(" - ");
}
