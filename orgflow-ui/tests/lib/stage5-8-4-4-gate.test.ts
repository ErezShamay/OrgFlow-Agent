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

describe("stage 5.8.4.4 gate (features card 4 - urban renewal QC)", () => {
  it("sharpens urban renewal card for TAMA stages and catalog-linked issues", () => {
    const source = readPublicHomePage();

    expect(source).toContain('title: "התחדשות עירונית"');
    expect(source).toContain('תמ\\"א, שלבי ביקור');
    expect(source).toContain("מפרט הנדסי");
    expect(source).toContain("סעיפי קטלוג");
    expect(source).not.toContain("פינוי-בינוי");
    expect(source).not.toContain("תהליכי עבודה מוכרים");
  });
});
