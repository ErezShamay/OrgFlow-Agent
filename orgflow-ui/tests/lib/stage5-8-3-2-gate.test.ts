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

describe("stage 5.8.3.2 gate (workflow pillars - issues)", () => {
  it("replaces operational actions pillar with live issue tracking", () => {
    const source = readPublicHomePage();

    expect(source).toContain('value: "ליקויים"');
    expect(source).toContain('label: "מעקב חי בין ביקורים"');
    expect(source).not.toContain('value: "פעולות תפעוליות"');
    expect(source).not.toContain("מעקב סטטוס, השלמה וחסימה");
  });
});
