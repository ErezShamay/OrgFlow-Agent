import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { getFrozenSurface } from "@/lib/qc-freeze";

const REPO_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(REPO_ROOT, relativePath), "utf8");
}

describe("stage 5.7 gate (findings upload → quality_issues)", () => {
  it("documents ai_upload_pipeline replacement as field reports + registry", () => {
    const surface = getFrozenSurface("ai_upload_pipeline");
    expect(surface?.qcReplacement).toContain("registry");
  });

  it("wires upload finding materialization into report processing", () => {
    const reportProcessing = readSource(
      "app/services/report_processing_service.py"
    );
    const uploadFindingService = readSource(
      "app/services/quality_issue_upload_finding_service.py"
    );
    const qualityIssueSchema = readSource("app/schemas/quality_issue.py");

    expect(uploadFindingService).toContain(
      "QualityIssueUploadFindingService"
    );
    expect(uploadFindingService).toContain('"ai_upload"');
    expect(reportProcessing).toContain("materialize_from_upload_finding");
    expect(reportProcessing).toContain("quality_issue_id");
    expect(qualityIssueSchema).toContain(
      "build_upload_finding_materialization_key"
    );
  });
});
