import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");
const PUBLIC_HOME_PAGE = path.join(
  UI_ROOT,
  "components/landing/PublicHomePage.tsx"
);

function readPublicHomePage(): string {
  return readFileSync(PUBLIC_HOME_PAGE, "utf8");
}

describe("stage 5.8.1.3 gate (hero subtitle - QC flow)", () => {
  it("describes visit report → issues → closure → QC portfolio", () => {
    const source = readPublicHomePage();

    expect(source).toMatch(
      /<h1[\s\S]*?<\/h1>[\s\S]*?דוח ביקור[\s\S]*?ליקויים חיים[\s\S]*?סגירה[\s\S]*?תיק בקרת איכות/
    );
    expect(source).not.toContain("פלטפורמת AI לתפעול פיקוח הנדסי");
    expect(source).not.toContain("מדוחות וחריגות");
  });
});
