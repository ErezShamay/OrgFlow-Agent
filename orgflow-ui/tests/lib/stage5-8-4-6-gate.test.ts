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

describe("stage 5.8.4.6 gate (features card 6 - QC portfolio)", () => {
  it("replaces multi-project management with QC portfolio ranking", () => {
    const source = readPublicHomePage();

    expect(source).toContain('title: "תיק בקרת איכות"');
    expect(source).toContain("דירוג פרויקטים לפי ליקויים");
    expect(source).toContain("חומרה");
    expect(source).not.toContain('title: "ניהול רב-פרויקטים"');
    expect(source).not.toContain("תצוגת פורטפolio מרכזית");
  });
});
