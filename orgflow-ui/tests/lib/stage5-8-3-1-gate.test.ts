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

describe("stage 5.8.3.1 gate (workflow pillars - field reports)", () => {
  it("replaces AI reviews pillar with field reports offline and PDF", () => {
    const source = readPublicHomePage();

    expect(source).toContain('value: "דוחות שטח"');
    expect(source).toContain('label: "עריכה offline, PDF"');
    expect(source).not.toContain('value: "ביקורות AI"');
    expect(source).not.toContain("פרשנות, אישור ודחייה מנהלתית");
  });
});
