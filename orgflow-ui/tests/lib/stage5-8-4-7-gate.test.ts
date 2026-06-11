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

describe("stage 5.8.4.7 gate (features section subtitle - QC)", () => {
  it("replaces operational AI engine tagline with field-first supervision", () => {
    const source = readPublicHomePage();

    expect(source).toContain("פיקוח שמתחיל בשטח");
    expect(source).toContain("מדוח ביקור וליקויים");
    expect(source).toContain("תיק QC לפרויקטים מורכבים");
    expect(source).not.toContain("מנוע AI תפעולי");
    expect(source).not.toContain("שמחבר בין דוחות, חריגות");
  });
});
