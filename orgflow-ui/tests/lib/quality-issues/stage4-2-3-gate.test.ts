import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  buildRemediationUpdateRequest,
  canSubmitRemediation,
} from "@/lib/quality-issues/issue-status-actions";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 4.2.3 gate (contractor remediation photo upload)", () => {
  it("requires remediation photos in update request and submit guard", () => {
    expect(
      buildRemediationUpdateRequest({
        notes: "בוצע תיקון",
        photo_ids: ["photo-1"],
      })
    ).toEqual({
      status: "PENDING_VERIFICATION",
      notes: "בוצע תיקון",
      photo_ids: ["photo-1"],
    });
    expect(canSubmitRemediation({ photoIds: [] })).toBe(false);
    expect(canSubmitRemediation({ photoIds: ["photo-1"] })).toBe(true);
  });

  it("wires remediation photo upload into contractor status actions", () => {
    const statusActions = readSource(
      "components/quality-issues/IssueStatusActions.tsx"
    );
    const uploadComponent = readSource(
      "components/quality-issues/RemediationPhotoUpload.tsx"
    );
    const uploadHelper = readSource(
      "lib/quality-issues/remediation-photo-upload.ts"
    );

    expect(statusActions).toContain("RemediationPhotoUpload");
    expect(statusActions).toContain("canSubmitRemediation");
    expect(statusActions).toContain("photo_ids: remediationPhotoIds");
    expect(uploadComponent).toContain("תמונת תיקון (חובה)");
    expect(uploadComponent).toContain("uploadRemediationPhoto");
    expect(uploadHelper).toContain("buildIssuePhotosPath");
  });
});
