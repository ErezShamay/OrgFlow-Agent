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

describe("stage 5.8.4.3 gate (features card 3 - professional PDF)", () => {
  it("replaces continuous engineering supervision with client-style PDF reports", () => {
    const source = readPublicHomePage();

    expect(source).toContain('title: "PDF מקצועי"');
    expect(source).toContain("דוגמאות לקוח");
    expect(source).toContain("FileText");
    expect(source).not.toContain('title: "פיקוח הנדסי רציף"');
    expect(source).not.toContain("שקיפות מלאה על מצב הפרויקט, נקודות סיכון");
  });
});
