import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");
const CTA_LINK = path.join(
  UI_ROOT,
  "components/landing/LandingSystemCtaLink.tsx"
);

function readCtaLinkSource(): string {
  return readFileSync(CTA_LINK, "utf8");
}

describe("stage 5.8.1.4 gate (hero CTA - QC field report entry)", () => {
  it("uses QC hero labels and routes authenticated users to field reports", () => {
    const source = readCtaLinkSource();

    expect(source).toContain('label: "התחל דוח שטח"');
    expect(source).toContain('label: "כניסה למערכת"');
    expect(source).toContain("FIELD_REPORTS_ROUTE.href");
    expect(source).toMatch(/variant === "hero"/);
    expect(source).not.toContain("שלוט בפרויקט");
  });
});
