import { describe, expect, it } from "vitest";

import {
  DEFAULT_MATCH_LIMIT,
  findOpenIssueMatches,
  matchKeyForFinding,
  rankMatchCandidates,
} from "@/lib/quality-issues/matching";
import type { QualityIssue, QualityIssueMatchCandidate } from "@/lib/quality-issues/types";

function sampleIssue(overrides: Partial<QualityIssue> = {}): QualityIssue {
  return {
    id: "issue-1",
    organization_id: "org-1",
    project_id: "proj-1",
    title: "נזילה",
    severity: "HIGH",
    status: "OPEN",
    location: "דירה 3",
    trade: "אינסטלציה",
    group_key: "bath",
    first_seen_report_id: "report-1",
    first_seen_at: "2026-06-01T10:00:00Z",
    last_seen_report_id: "report-1",
    last_seen_at: "2026-06-01T10:00:00Z",
    recurrence_count: 0,
    photo_ids: [],
    created_at: "2026-06-01T10:00:00Z",
    updated_at: "2026-06-01T10:00:00Z",
    ...overrides,
  };
}

describe("quality issue matching (offline, 2.1.7)", () => {
  it("matches by normalized location + trade + group_key only", () => {
    const openIssues = [
      sampleIssue({ id: "match", location: " דירה 3 " }),
      sampleIssue({
        id: "other-location",
        location: "דירה 4",
      }),
      sampleIssue({
        id: "closed",
        status: "CLOSED",
      }),
    ];

    const candidates = findOpenIssueMatches(
      {
        location: "דירה 3",
        trade: "אינסטלציה",
        group_key: "bath",
      },
      openIssues
    );

    expect(candidates).toHaveLength(2);
    expect(candidates.map((candidate) => candidate.issue.id)).toEqual([
      "match",
      "closed",
    ]);
    expect(candidates[0]?.match_key).toBe(
      matchKeyForFinding({
        location: "דירה 3",
        trade: "אינסטלציה",
        group_key: "bath",
      })
    );
  });

  it("ranks by severity, catalog match, and recency", () => {
    const candidates: QualityIssueMatchCandidate[] = [
      {
        issue: sampleIssue({
          id: "medium-old",
          severity: "MEDIUM",
          catalog_issue_id: null,
          last_seen_at: "2026-06-01T10:00:00Z",
        }),
        match_key: "d|t|g",
        score: 1,
      },
      {
        issue: sampleIssue({
          id: "critical-catalog",
          severity: "CRITICAL",
          catalog_issue_id: "STR-001",
          last_seen_at: "2026-05-01T10:00:00Z",
        }),
        match_key: "d|t|g",
        score: 1,
      },
      {
        issue: sampleIssue({
          id: "high-recent",
          severity: "HIGH",
          catalog_issue_id: null,
          last_seen_at: "2026-06-08T10:00:00Z",
        }),
        match_key: "d|t|g",
        score: 1,
      },
    ];

    const ranked = rankMatchCandidates(candidates, "STR-001");
    expect(ranked.map((candidate) => candidate.issue.id)).toEqual([
      "critical-catalog",
      "high-recent",
      "medium-old",
    ]);
  });

  it("respects match limit", () => {
    const openIssues = Array.from({ length: 8 }, (_, index) =>
      sampleIssue({ id: `issue-${index}` })
    );

    const candidates = findOpenIssueMatches(
      {
        location: "דירה 3",
        trade: "אינסטלציה",
        group_key: "bath",
      },
      openIssues,
      3
    );

    expect(candidates).toHaveLength(3);
    expect(DEFAULT_MATCH_LIMIT).toBe(5);
  });
});
