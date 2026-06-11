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

describe("stage 5.8.1.1 gate (hero badge - QC positioning)", () => {
  it("shows QC badge instead of AI operations tagline", () => {
    const source = readPublicHomePage();

    expect(source).toContain("בקרת איכות לפרויקטי בנייה");
    expect(source).not.toContain("מערכת תפעול הנדסי מבוססת AI");
  });
});
