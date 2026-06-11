import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../..");

const HOME_PAGE_SOURCE_FILES = [
  "app/page.tsx",
  "components/landing/PublicHomePage.tsx",
  "components/landing/PublicNavBar.tsx",
  "components/landing/HeroDashboardPreview.tsx",
  "components/landing/LandingSystemCtaLink.tsx",
  "components/landing/HomeScrollManager.tsx",
] as const;

const REQUIRED_QC_HOME_PAGE_TERMS = [
  "ליקוי",
  "דוח שטח",
  "בקרת איכות",
] as const;

function readHomePageSources(): string {
  return HOME_PAGE_SOURCE_FILES.map((relativePath) =>
    readFileSync(path.join(UI_ROOT, relativePath), "utf8")
  ).join("\n");
}

describe("stage 5.8.9.2 gate (home page - QC messaging present)", () => {
  it("home page sources include issue tracking, field reports and quality control", () => {
    const source = readHomePageSources();

    for (const term of REQUIRED_QC_HOME_PAGE_TERMS) {
      expect(source).toContain(term);
    }
  });
});
