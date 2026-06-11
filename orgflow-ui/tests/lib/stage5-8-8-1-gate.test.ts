import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");
const ROOT_LAYOUT = path.join(UI_ROOT, "app/layout.tsx");
const ELAYOAI_KEYS = path.join(UI_ROOT, "lib/elayoai/keys.ts");

describe("stage 5.8.8.1 gate (metadata description - QC)", () => {
  it("describes quality control platform instead of construction management", () => {
    const layout = readFileSync(ROOT_LAYOUT, "utf8");
    const keys = readFileSync(ELAYOAI_KEYS, "utf8");

    expect(keys).toContain("export const ELAYOAI_APP_DESCRIPTION =");
    expect(keys).toContain(
      "Quality Control Platform for Construction Projects"
    );
    expect(layout).toContain("ELAYOAI_APP_DESCRIPTION");
    expect(layout).toContain("description: ELAYOAI_APP_DESCRIPTION");
    expect(keys).not.toContain("Construction Management");
    expect(layout).not.toContain("AI Operations Platform for Construction Management");
  });
});
