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

describe("stage 5.8.5.2 gate (workflow step 02 - report close to registry)", () => {
  it("replaces AI review with closed report materializing issues into registry", () => {
    const source = readPublicHomePage();

    expect(source).toContain('title: "סגירת דוח → ליקויים ב-registry"');
    expect(source).toContain("registry");
    expect(source).toContain("ליקוי חי");
    expect(source).not.toContain('title: "ממצאים וביקורת AI"');
    expect(source).not.toContain("ה-AI מחלץ ממצאים");
    expect(source).not.toContain("בלוח ביקורות AI");
  });
});
