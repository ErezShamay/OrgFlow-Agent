import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("visit report issue diff UI gate (2.3.3)", () => {
  it("wires visit diff panel into closed field report page", () => {
    const reportPage = readUiSource(
      "app/(dashboard)/field-reports/[id]/page.tsx"
    );
    const diffPanel = readUiSource(
      "components/quality-issues/VisitReportIssueDiffPanel.tsx"
    );
    const apiClient = readUiSource("lib/quality-issues/api.ts");
    const helpers = readUiSource("lib/quality-issues/visit-issue-diff.ts");

    expect(reportPage).toContain("VisitReportIssueDiffPanel");
    expect(reportPage).toContain("shouldShowVisitIssueDiff");
    expect(reportPage).toContain("serverVisitReportId(report)");
    expect(diffPanel).toContain("getProjectVisitIssueDiff");
    expect(diffPanel).toContain("שינויי ליקויים בביקור זה");
    expect(diffPanel).toContain("buildIssueDetailHref");
    expect(apiClient).toContain("buildProjectVisitIssueDiffPath");
    expect(apiClient).toContain("getProjectVisitIssueDiff");
    expect(helpers).toContain("shouldShowVisitIssueDiff");
  });
});
