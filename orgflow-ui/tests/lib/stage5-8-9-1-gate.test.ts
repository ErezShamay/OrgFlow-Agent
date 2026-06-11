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

const FORBIDDEN_HOME_PAGE_TERMS = [
  "פעולות תפעוליות",
  "אוטומציה",
] as const;

function readHomePageSources(): string {
  return HOME_PAGE_SOURCE_FILES.map((relativePath) =>
    readFileSync(path.join(UI_ROOT, relativePath), "utf8")
  ).join("\n");
}

describe("stage 5.8.9.1 gate (home page - no PM/automation copy)", () => {
  it("home page sources omit operational actions and automation messaging", () => {
    const source = readHomePageSources();

    for (const term of FORBIDDEN_HOME_PAGE_TERMS) {
      expect(source).not.toContain(term);
    }
  });
});
