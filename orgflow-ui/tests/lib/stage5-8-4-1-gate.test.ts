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

describe("stage 5.8.4.1 gate (features card 1 - field visit reports)", () => {
  it("replaces AI reviews feature with offline field visit reports", () => {
    const source = readPublicHomePage();

    expect(source).toContain('title: "דוחות ביקור בשטח"');
    expect(source).toContain("offline");
    expect(source).toContain("תמונות");
    expect(source).toContain("צ'קליסט");
    expect(source).toContain("ClipboardList");
    expect(source).not.toContain('title: "ביקורות AI אוטומטיות"');
    expect(source).not.toContain("ניתוח דוחות הנדסיים, זיהוי חריגות וסיכונים");
  });
});
