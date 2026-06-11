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

describe("stage 5.8.2.3 gate (hero mockup floating bubble - QC)", () => {
  it("shows new plumbing issue instead of execution delay deviation", () => {
    const source = readHeroPreview();

    expect(source).toContain("ליקוי חדש");
    expect(source).toContain("אינסטלציה");
    expect(source).not.toContain("חריגה חדשה");
    expect(source).not.toContain("עיכוב ביצוע");
  });
});
