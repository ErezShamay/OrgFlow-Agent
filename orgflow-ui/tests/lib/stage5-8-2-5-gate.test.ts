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

describe("stage 5.8.2.5 gate (hero mockup project name - TAMA)", () => {
  it("shows a real TAMA project name from sample reports", () => {
    const source = readHeroPreview();

    expect(source).toContain("האורנים 7 הוד השרון");
    expect(source).not.toContain("מגדלי הים");
  });
});
