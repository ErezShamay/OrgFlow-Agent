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

describe("stage 5.8.6.3 gate (platform bullets - QC)", () => {
  it("lists QC capabilities instead of PM dashboards and automation", () => {
    const source = readPublicHomePage();

    expect(source).toContain("const PLATFORM_BULLETS = [");
    expect(source).toContain("ליקויים פתוחים לפי חומרה");
    expect(source).toContain("דוחות PDF");
    expect(source).toContain("מעקב בין ביקורים");
    expect(source).toContain("עבודה offline");
    expect(source).toContain("PLATFORM_BULLETS.map");
    expect(source).not.toContain("דשבורד KPI לכל פרויקט");
    expect(source).not.toContain("מעקב חריגות ואסקלציות");
    expect(source).not.toContain("התראות ועדכונים בזמן אמת");
    expect(source).not.toContain("אוטומציה ותורים חכמים");
  });
});
