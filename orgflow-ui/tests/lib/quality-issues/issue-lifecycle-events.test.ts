import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("issue lifecycle events UI gate (2.2.5)", () => {
  it("wires lifecycle event details into issue detail timeline", () => {
    const timeline = readUiSource(
      "components/quality-issues/IssueEventsTimeline.tsx"
    );
    const detailPanel = readUiSource(
      "components/quality-issues/IssueDetailPanel.tsx"
    );
    const issueDetail = readUiSource("lib/quality-issues/issue-detail.ts");

    expect(detailPanel).toContain("IssueEventsTimeline");
    expect(timeline).toContain("formatQualityIssueEventDetails");
    expect(issueDetail).toContain("LIFECYCLE_CLOSURE_EVENT_TYPES");
    expect(issueDetail).toContain("REMEDIATION_SUBMITTED");
    expect(issueDetail).toContain("VERIFIED_CLOSED");
    expect(issueDetail).toContain("REOPENED");
  });
});
