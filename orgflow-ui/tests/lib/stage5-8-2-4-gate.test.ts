import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");
const HERO_PREVIEW = path.join(
  UI_ROOT,
  "components/landing/HeroDashboardPreview.tsx"
);

function readHeroPreview(): string {
  return readFileSync(HERO_PREVIEW, "utf8");
}

describe("stage 5.8.2.4 gate (hero mockup second bubble - QC closure)", () => {
  it("shows visit closure with remediation photo instead of AI recommendations", () => {
    const source = readHeroPreview();

    expect(source).toContain("נסגר בביקור");
    expect(source).toContain("תמונת תיקון");
    expect(source).not.toContain("AI Insight");
    expect(source).not.toContain("3 פעולות מומלצות");
  });
});
