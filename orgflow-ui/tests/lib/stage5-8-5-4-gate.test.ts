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

describe("stage 5.8.5.4 gate (workflow step 04 - QC portfolio)", () => {
  it("replaces escalation tracking with QC portfolio overview", () => {
    const source = readPublicHomePage();

    expect(source).toContain('title: "תיק QC - תמונת מצב"');
    expect(source).toContain("ליקויים קריטיים");
    expect(source).toContain("דוחות ביקור");
    expect(source).not.toContain('title: "מעקב, הסלמה וסגירה"');
    expect(source).not.toContain("עוקבים אחר פעולות פתוחות ונקודות סיכון");
  });
});
