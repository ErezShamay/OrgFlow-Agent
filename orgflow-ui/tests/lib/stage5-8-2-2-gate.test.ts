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

describe("stage 5.8.2.2 gate (hero mockup chart - QC)", () => {
  it("shows issue closure trend instead of deviation closure trend", () => {
    const source = readHeroPreview();

    expect(source).toContain("מגמת סגירת ליקויים");
    expect(source).not.toContain("מגמת סגירת חריגות");
  });
});
