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

describe("stage 5.8.6.1 gate (platform section title - QC)", () => {
  it("replaces operating system headline with quality control platform", () => {
    const source = readPublicHomePage();

    expect(source).toMatch(
      /id="platform"[\s\S]*?פלטפורמת בקרת איכות/
    );
    expect(source).not.toContain("מערכת ההפעלה");
    expect(source).not.toContain("לפרויקטים שלך");
  });
});
