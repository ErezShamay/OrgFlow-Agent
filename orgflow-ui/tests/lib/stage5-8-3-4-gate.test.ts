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

describe("stage 5.8.3.4 gate (workflow pillars - QC portfolio)", () => {
  it("replaces automation pillar with QC portfolio severity overview", () => {
    const source = readPublicHomePage();

    expect(source).toContain('value: "תיק QC"');
    expect(source).toContain('label: "תמונת מצב לפי חומרה"');
    expect(source).not.toContain('value: "אוטומציה"');
    expect(source).not.toContain("תורים, ניטור בריאות ו-Dead Letters");
  });
});
