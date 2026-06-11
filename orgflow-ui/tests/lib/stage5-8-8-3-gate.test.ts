import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");
const BRAND_LOGO = path.join(UI_ROOT, "components/ui/BrandLogo.tsx");
const ELAYOAI_KEYS = path.join(UI_ROOT, "lib/elayoai/keys.ts");

describe("stage 5.8.8.3 gate (BrandLogo tagline - QC)", () => {
  it("keeps app name and shows QC tagline from shared keys", () => {
    const logo = readFileSync(BRAND_LOGO, "utf8");
    const keys = readFileSync(ELAYOAI_KEYS, "utf8");

    expect(keys).toContain('export const ELAYOAI_APP_TAGLINE =');
    expect(keys).toContain("בקרת איכות לפרויקטי בנייה");
    expect(logo).toContain("ELAYOAI_APP_NAME");
    expect(logo).toContain("ELAYOAI_APP_TAGLINE");
    expect(logo).not.toContain("AI לניהול בנייה ותפעול שטח");
    expect(logo).not.toContain("ניהול תפעול");
  });
});
