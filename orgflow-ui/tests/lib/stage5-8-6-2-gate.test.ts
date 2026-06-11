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

describe("stage 5.8.6.2 gate (platform description - QC)", () => {
  it("describes field reports, issues, closure and QC portfolio without automation", () => {
    const source = readPublicHomePage();

    expect(source).toContain(
      "ממשק אחיד לדוחות שטח, מעקב ליקויים,"
    );
    expect(source).toContain(
      "סגירה ואימות ותיק בקרת איכות - מהביקור"
    );
    expect(source).not.toContain("ממשק אחיד לניהול ביקורות, חריגות");
    expect(source).not.toContain("פעולות תפעוליות והתראות");
  });
});
