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

describe("stage 5.8.7.1 gate (final CTA headline - QC)", () => {
  it("replaces project control headline with quality control", () => {
    const source = readPublicHomePage();

    expect(source).toContain("const FINAL_CTA = {");
    expect(source).toContain('headline: "מוכנים לשלוט באיכות?"');
    expect(source).toContain("FINAL_CTA.headline");
    expect(source).not.toContain("מוכנים לשלוט בפרויקט?");
  });
});
