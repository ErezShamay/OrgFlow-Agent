import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const QC_SPEC_ROOT = join(process.cwd(), "..", "docs", "qc-spec");

const QC_SPEC_DOCUMENTS = [
  "qc-platform-spec.md",
  "quality-issue-model.md",
  "quality-issue-events.md",
  "qc-personas-permissions.md",
  "qc-navigation.md",
  "qc-freeze-list.md",
];

describe("qc spec gate (0.6)", () => {
  it("has all spec documents on disk", () => {
    const missing = QC_SPEC_DOCUMENTS.filter(
      (name) => !existsSync(join(QC_SPEC_ROOT, name))
    );
    expect(missing).toEqual([]);
  });

  it("consolidated spec references MVP and stage 1", () => {
    const content = readFileSync(
      join(QC_SPEC_ROOT, "qc-platform-spec.md"),
      "utf-8"
    );
    expect(content).toContain("שלב 1");
    expect(content).toContain("quality_issue");
    expect(content).toContain("מאושר ליישום");
  });
});
