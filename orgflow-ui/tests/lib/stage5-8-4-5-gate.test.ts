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

describe("stage 5.8.4.5 gate (features card 5 - issue closure)", () => {
  it("replaces operational automation with visit-to-visit issue closure", () => {
    const source = readPublicHomePage();

    expect(source).toContain('title: "סגירת ליקויים"');
    expect(source).toContain("ביקור לביקור");
    expect(source).toContain("ליקוי חוזר");
    expect(source).toContain("CheckCircle2");
    expect(source).not.toContain('title: "אוטומציה תפעולית"');
    expect(source).not.toContain("הפקת פעולות, התראות ודוחות");
  });
});
