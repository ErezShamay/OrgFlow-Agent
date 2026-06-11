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

describe("stage 5.8.7.3 gate (footer tagline - QC)", () => {
  it("replaces operational engineering tagline with quality control", () => {
    const source = readPublicHomePage();

    expect(source).toContain(
      'const FOOTER_TAGLINE = "בקרת איכות לפרויקטי בנייה"'
    );
    expect(source).toMatch(/<footer[\s\S]*?FOOTER_TAGLINE/);
    expect(source).not.toContain("פלטפורמת AI לניהול תפעול הנדסי");
    expect(source).not.toContain("ניהול תפעול הנדסי");
  });
});
