import { describe, expect, it } from "vitest";

import {
  buildProjectIssueHref,
  formatContractorRecurringSubtitle,
  formatRecurringIssueSubtitle,
  formatRecurringRankingsCaption,
} from "@/lib/quality-issues/recurring-rankings";
import type {
  QualityContractorRecurringRankEntry,
  QualityRecurringIssueRankEntry,
  QualityRecurringRankingsResponse,
} from "@/lib/quality-issues/types";

const sampleIssue: QualityRecurringIssueRankEntry = {
  issue_id: "issue-1",
  title: "נזילה חוזרת",
  trade: "אינסטלציה",
  location: "קומה 2",
  recurrence_count: 2,
  project_id: "proj-1",
  project_name: "האורנים 7",
  contractor_name: "קבלנות כהן",
  status: "REOPENED",
  severity: "CRITICAL",
};

const sampleContractor: QualityContractorRecurringRankEntry = {
  contractor_name: "קבלנות כהן",
  recurring_issue_count: 3,
  total_recurrence_count: 5,
  project_count: 2,
};

describe("recurring rankings helpers", () => {
  it("formats empty caption when no recurring issues", () => {
    const response: QualityRecurringRankingsResponse = {
      organization_id: "org-1",
      project_id: null,
      total_recurring: 0,
      issues: [],
      contractors: [],
    };

    expect(formatRecurringRankingsCaption(response)).toBe(
      "אין ליקויים חוזרים בתיק"
    );
  });

  it("formats caption with top contractor pressure", () => {
    const response: QualityRecurringRankingsResponse = {
      organization_id: "org-1",
      project_id: null,
      total_recurring: 4,
      issues: [sampleIssue],
      contractors: [sampleContractor],
    };

    expect(formatRecurringRankingsCaption(response)).toContain("4 ליקויים חוזרים");
    expect(formatRecurringRankingsCaption(response)).toContain("קבלנות כהן");
  });

  it("formats issue and contractor subtitles", () => {
    expect(formatRecurringIssueSubtitle(sampleIssue)).toBe(
      "האורנים 7 · אינסטלציה · קבלנות כהן"
    );
    expect(formatContractorRecurringSubtitle(sampleContractor)).toBe(
      "2 פרויקטים · 5 אירועי חזרה"
    );
  });

  it("builds project issue href", () => {
    expect(buildProjectIssueHref("proj-1", "issue-1")).toBe(
      "/projects/proj-1/issues/issue-1"
    );
  });
});
