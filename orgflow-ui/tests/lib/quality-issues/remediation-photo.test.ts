import { describe, expect, it } from "vitest";

import {
  buildIssuePhotoPath,
  buildIssuePhotosPath,
} from "@/lib/quality-issues/api";
import { canSubmitRemediation } from "@/lib/quality-issues/issue-status-actions";
import { remediationPhotoFilename } from "@/lib/quality-issues/remediation-photo";

describe("remediation photo helpers (4.2.3)", () => {
  it("builds issue photo API paths", () => {
    expect(buildIssuePhotosPath("issue-1")).toBe("/issues/issue-1/photos");
    expect(buildIssuePhotoPath("issue-1", "photo-1")).toBe(
      "/issues/issue-1/photos/photo-1"
    );
  });

  it("maps remediation filenames by mime type", () => {
    expect(remediationPhotoFilename("image/png")).toBe("remediation.png");
    expect(remediationPhotoFilename("image/webp")).toBe("remediation.webp");
    expect(remediationPhotoFilename("image/jpeg")).toBe("remediation.jpg");
  });

  it("requires at least one remediation photo before submit", () => {
    expect(canSubmitRemediation({ photoIds: [] })).toBe(false);
    expect(canSubmitRemediation({ photoIds: ["photo-1"] })).toBe(true);
  });
});
