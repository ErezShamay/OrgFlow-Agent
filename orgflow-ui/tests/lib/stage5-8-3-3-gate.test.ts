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

describe("stage 5.8.3.3 gate (workflow pillars - closure verification)", () => {
  it("replaces risk points pillar with contractor and supervisor closure flow", () => {
    const source = readPublicHomePage();

    expect(source).toContain('value: "סגירה ואימות"');
    expect(source).toContain('label: "קבלן + מפקח"');
    expect(source).not.toContain('value: "נקודות סיכון"');
    expect(source).not.toContain("הסלמה ידנית ואוטומטית לפי SLA");
  });
});
