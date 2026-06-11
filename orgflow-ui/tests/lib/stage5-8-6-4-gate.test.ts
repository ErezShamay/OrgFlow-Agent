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

describe("stage 5.8.6.4 gate (platform field card - QC)", () => {
  it("replaces Operational AI Engine with field-ready QC messaging", () => {
    const source = readPublicHomePage();

    expect(source).toContain("const PLATFORM_FIELD_CARD = {");
    expect(source).toContain('title: "מוכן לשטח"');
    expect(source).toMatch(
      /id="platform"[\s\S]*?PLATFORM_FIELD_CARD\.title/
    );
    expect(source).toContain("PLATFORM_FIELD_CARD.title");
    expect(source).toContain("PLATFORM_FIELD_CARD.description");
    expect(source).not.toContain("Operational AI Engine");
    expect(source).not.toContain("מוכן לעבודה");
    expect(source).not.toContain("לכל שכבות התפעול");
    expect(source).not.toContain("System Online");
  });
});
