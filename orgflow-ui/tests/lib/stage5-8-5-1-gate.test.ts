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

describe("stage 5.8.5.1 gate (workflow step 01 - field visit report)", () => {
  it("replaces project intake with supervisor creating a field visit report", () => {
    const source = readPublicHomePage();

    expect(source).toContain('title: "מפקח יוצר דוח ביקור בשטח"');
    expect(source).toContain("תמונות");
    expect(source).toContain("ממצאים");
    expect(source).toContain("צ'קליסט");
    expect(source).not.toContain('title: "הקשר פרויקט וקליטת חומר"');
    expect(source).not.toContain("מעלים דוח הנדסי או מסמך תפעולי");
  });
});
