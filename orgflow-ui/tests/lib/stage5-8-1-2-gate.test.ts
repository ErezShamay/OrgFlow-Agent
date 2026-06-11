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

describe("stage 5.8.1.2 gate (hero H1 - QC positioning)", () => {
  it("shows QC headline instead of enterprise engineering supervision", () => {
    const source = readPublicHomePage();

    expect(source).toMatch(
      /<h1[\s\S]*?>[\s\S]*?בקרת איכות[\s\S]*?בשטח[\s\S]*?<\/h1>/
    );
    expect(source).not.toContain("ברמת Enterprise");
  });
});
