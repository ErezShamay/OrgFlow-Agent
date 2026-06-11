import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("finding line issue status UI gate (2.2.6)", () => {
  it("wires visit-line closure actions into finding row editors", () => {
    const hint = readUiSource(
      "components/quality-issues/FindingSimilarIssuesHint.tsx"
    );
    const statusActions = readUiSource(
      "components/quality-issues/FindingLinkedIssueStatusActions.tsx"
    );
    const lineEditor = readUiSource(
      "components/field-reports/ReportLineEditor.tsx"
    );
    const findingsEditor = readUiSource(
      "components/field-reports/ReportFindingsBlockEditor.tsx"
    );
    const helpers = readUiSource(
      "lib/quality-issues/finding-line-issue-actions.ts"
    );

    expect(hint).toContain("FindingLinkedIssueStatusActions");
    expect(hint).toContain("reportId={reportId}");
    expect(hint).toContain("lineId={lineId}");
    expect(statusActions).toContain("getFindingLineIssueStatusActions");
    expect(statusActions).toContain("resolveLinkedIssueForFindingLine");
    expect(lineEditor).toContain("reportId={reportId}");
    expect(lineEditor).toContain("lineId={line.id}");
    expect(findingsEditor).toContain("reportId={reportId}");
    expect(helpers).toContain("סמן כנסגר");
    expect(helpers).toContain("אשר סגירה");
    expect(helpers).toContain("חזר");
  });
});
