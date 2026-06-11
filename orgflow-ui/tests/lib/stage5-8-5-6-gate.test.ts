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

describe("stage 5.8.5.6 gate (how-it-works subtitle - QC flow)", () => {
  it("replaces AI and operational actions path with QC workflow", () => {
    const source = readPublicHomePage();

    expect(source).toContain("דוח ביקור בשטח");
    expect(source).toContain("ליקויים ב-registry");
    expect(source).toContain("סגירה ואימות");
    expect(source).toContain("תיק QC");
    expect(source).not.toContain("ביקורת AI");
    expect(source).not.toContain("פעולות תפעוליות → מעקב והסלמה");
  });
});
