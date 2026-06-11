import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");
const APP_MANIFEST = path.join(UI_ROOT, "app/manifest.ts");
const ELAYOAI_KEYS = path.join(UI_ROOT, "lib/elayoai/keys.ts");

describe("stage 5.8.8.2 gate (PWA manifest - QC)", () => {
  it("uses QC name and description in app manifest", () => {
    const manifest = readFileSync(APP_MANIFEST, "utf8");
    const keys = readFileSync(ELAYOAI_KEYS, "utf8");

    expect(keys).toContain("export const ELAYOAI_MANIFEST_NAME =");
    expect(keys).toContain("export const ELAYOAI_MANIFEST_DESCRIPTION =");
    expect(keys).toContain("בקרת איכות לפרויקטי בנייה");
    expect(keys).toContain("דוחות שטח, מעקב ליקויים");
    expect(manifest).toContain("ELAYOAI_MANIFEST_NAME");
    expect(manifest).toContain("ELAYOAI_MANIFEST_DESCRIPTION");
    expect(manifest).toContain("short_name: ELAYOAI_APP_NAME");
    expect(manifest).not.toContain("דוחות שטח ועריכה במצב רשת/אופליין");
  });
});
