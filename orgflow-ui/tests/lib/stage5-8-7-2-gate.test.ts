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

describe("stage 5.8.7.2 gate (final CTA subheadline - QC)", () => {
  it("prompts first field visit report instead of operational workspace access", () => {
    const source = readPublicHomePage();

    expect(source).toContain(
      'subheadline: "התחברו וצרו דוח ביקור ראשון"'
    );
    expect(source).toContain("FINAL_CTA.subheadline");
    expect(source).not.toContain("התחברו למערכת וקבלו גישה מיידית");
    expect(source).not.toContain("לסביבת העבודה התפעולית");
  });
});
