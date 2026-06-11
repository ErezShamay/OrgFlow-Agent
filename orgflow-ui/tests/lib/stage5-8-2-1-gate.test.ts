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

describe("stage 5.8.2.1 gate (hero mockup KPIs - QC)", () => {
  it("shows field reports, open issues, and closure rate instead of AI reviews", () => {
    const source = readHeroPreview();

    expect(source).toContain('label: "דוחות שטח"');
    expect(source).toContain('label: "ליקויים פתוחים"');
    expect(source).toContain('label: "% סגירה"');
    expect(source).not.toContain("ביקורות AI");
    expect(source).not.toContain('label: "חריגות"');
    expect(source).not.toContain('label: "סגירות"');
  });
});
