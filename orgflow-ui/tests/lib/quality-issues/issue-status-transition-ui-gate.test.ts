import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("issue status transition UI gate (2.2.1–2.2.4)", () => {
  it("wires start-remediation action into issue detail panel", () => {
    const detailPanel = readUiSource(
      "components/quality-issues/IssueDetailPanel.tsx"
    );
    const detailPage = readUiSource(
      "app/(dashboard)/projects/[id]/issues/[issueId]/page.tsx"
    );
    const statusActions = readUiSource(
      "components/quality-issues/IssueStatusActions.tsx"
    );
    const statusActionHelpers = readUiSource(
      "lib/quality-issues/issue-status-actions.ts"
    );

    expect(detailPanel).toContain("IssueStatusActions");
    expect(detailPanel).toContain("actorRole");
    expect(detailPage).toContain("actorRole={effectiveRole}");
    expect(detailPage).toContain("onIssueUpdated={() => reload()}");
    expect(statusActions).toContain("buildRemediationUpdateRequest");
    expect(statusActions).toContain("RemediationPhotoUpload");
    expect(statusActions).toContain("canSubmitRemediation");
    expect(statusActions).toContain("שלח לבדיקת מפקח");
    expect(statusActions).toContain("buildVerifyCloseUpdateRequest");
    expect(statusActions).toContain("buildReopenUpdateRequest");
    expect(statusActions).toContain("הליקוי נסגר לאחר אימות התיקון");
    expect(statusActions).toContain("הליקוי סומן כליקוי חוזר");
    expect(statusActionHelpers).toContain("אשר סגירה");
    expect(statusActionHelpers).toContain("verify-close");
    expect(statusActionHelpers).toContain("סמן כחוזר");
    expect(statusActionHelpers).toContain("reopen-issue");
  });
});
