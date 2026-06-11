/**
 * Client-side matching for open registry issues (mirrors backend matching service).
 * Used when suggest-matches API is unavailable offline.
 */

import {
  buildMatchKey,
  severityRank,
  type FindingMatchInput,
  type QualityIssue,
  type QualityIssueMatchCandidate,
} from "@/lib/quality-issues/types";

export const DEFAULT_MATCH_LIMIT = 5;
export const EXACT_MATCH_SCORE = 1;

function normalizeCatalogId(value: string | null | undefined): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed.toLowerCase() : "";
}

function parseTimestamp(value: string | null | undefined): number {
  if (!value?.trim()) {
    return 0;
  }

  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function candidateSortKey(
  candidate: QualityIssueMatchCandidate,
  findingCatalogIssueId: string | null | undefined
): [number, number, number, string] {
  const issue = candidate.issue;
  const severity = severityRank(issue.severity);
  const findingCatalog = normalizeCatalogId(findingCatalogIssueId);
  const issueCatalog = normalizeCatalogId(issue.catalog_issue_id);
  const catalogBoost = Number(
    Boolean(findingCatalog) && findingCatalog === issueCatalog
  );
  const lastSeenEpoch = parseTimestamp(issue.last_seen_at);

  return [-severity, -catalogBoost, -lastSeenEpoch, issue.title];
}

export function matchKeyForFinding(finding: FindingMatchInput): string {
  return buildMatchKey({
    location: finding.location,
    trade: finding.trade,
    group_key: finding.group_key,
  });
}

export function matchKeyForIssue(issue: QualityIssue): string {
  return buildMatchKey({
    location: issue.location,
    trade: issue.trade,
    group_key: issue.group_key,
  });
}

export function rankMatchCandidates(
  candidates: QualityIssueMatchCandidate[],
  findingCatalogIssueId?: string | null
): QualityIssueMatchCandidate[] {
  return [...candidates].sort((left, right) => {
    const leftKey = candidateSortKey(left, findingCatalogIssueId);
    const rightKey = candidateSortKey(right, findingCatalogIssueId);

    for (let index = 0; index < leftKey.length; index += 1) {
      if (leftKey[index] < rightKey[index]) {
        return -1;
      }
      if (leftKey[index] > rightKey[index]) {
        return 1;
      }
    }

    return 0;
  });
}

export function findOpenIssueMatches(
  finding: FindingMatchInput,
  openIssues: QualityIssue[],
  limit: number = DEFAULT_MATCH_LIMIT
): QualityIssueMatchCandidate[] {
  const targetKey = matchKeyForFinding(finding);
  const candidates: QualityIssueMatchCandidate[] = [];

  for (const issue of openIssues) {
    const issueKey = matchKeyForIssue(issue);
    if (issueKey !== targetKey) {
      continue;
    }

    candidates.push({
      issue,
      match_key: issueKey,
      score: EXACT_MATCH_SCORE,
    });
  }

  const ranked = rankMatchCandidates(
    candidates,
    finding.catalog_issue_id
  );
  return ranked.slice(0, Math.max(limit, 0));
}
