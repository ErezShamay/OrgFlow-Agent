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

describe("stage 5.8.5.5 gate (how-it-works section title - QC)", () => {
  it("replaces action closure headline with field visit to closed issue flow", () => {
    const source = readPublicHomePage();

    expect(source).toContain("מביקור בשטח ועד ליקוי סגור");
    expect(source).not.toContain("מקליטת דוח ועד סגירת פעולה");
  });
});
