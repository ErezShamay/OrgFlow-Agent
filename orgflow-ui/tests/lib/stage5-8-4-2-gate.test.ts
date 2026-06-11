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

describe("stage 5.8.4.2 gate (features card 2 - issue tracking)", () => {
  it("replaces smart deviation analysis with live issue registry tracking", () => {
    const source = readPublicHomePage();

    expect(source).toContain('title: "מעקב ליקויים"');
    expect(source).toContain("registry");
    expect(source).toContain("חומרה");
    expect(source).toContain("מיקום");
    expect(source).toContain("מלאכה");
    expect(source).toContain("AlertTriangle");
    expect(source).not.toContain('title: "ניתוח חריגות חכם"');
    expect(source).not.toContain("מיפוי, סיווג ומעקב אחר חריגות בפרויקט");
  });
});
