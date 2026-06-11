import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { GLOBAL_NAV_LINKS } from "@/lib/navigation";
import { getQCPrimaryNavLinks } from "@/lib/qc-navigation";

const UI_ROOT = path.resolve(__dirname, "../..");

const HOME_PAGE_SOURCE_FILES = [
  "app/page.tsx",
  "components/landing/PublicHomePage.tsx",
  "components/landing/PublicNavBar.tsx",
  "components/landing/HeroDashboardPreview.tsx",
  "components/landing/LandingSystemCtaLink.tsx",
  "components/landing/HomeScrollManager.tsx",
] as const;

const FORBIDDEN_HOME_VALUE_TERMS = [
  "ניהול פרויקטים",
  "אוטומציה",
  "פעולות תפעוליות",
] as const;

const QC_WORKFLOW_STEP_TITLES = [
  "מפקח יוצר דוח ביקור בשטח",
  "סגירת דוח → ליקויים ב-registry",
  "מעקב סגירה - קבלן ומפקח",
  "תיק QC - תמונת מצב",
] as const;

const QC_WORKFLOW_PILLAR_VALUES = [
  "דוחות שטח",
  "ליקויים",
  "סגירה ואימות",
  "תיק QC",
] as const;

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

function readHomePageSources(): string {
  return HOME_PAGE_SOURCE_FILES.map((relativePath) => readSource(relativePath)).join(
    "\n"
  );
}

describe("stage 5 gate (PM cleanup + QC positioning)", () => {
  it("home page leads with supervision messaging, not project management", () => {
    const homePage = readSource("components/landing/PublicHomePage.tsx");
    const cta = readSource("components/landing/LandingSystemCtaLink.tsx");

    expect(homePage).toContain("בקרת איכות בשטח");
    expect(homePage).toContain("מדוח ביקור בשטח → ליקויים חיים בין ביקורים");
    expect(homePage).toContain("פיקוח שמתחיל בשטח");
    expect(cta).toContain("התחל דוח שטח");
    expect(homePage).not.toContain("שלוט בפרויקט");
    expect(cta).not.toContain("שלוט בפרויקט");
  });

  it("primary navigation has at most four QC routes", () => {
    const fullAccessRoles = ["SUPERVISOR", "DEVELOPER", "ADMIN"] as const;
    const personas = [...fullAccessRoles, "CONTRACTOR"] as const;

    expect(GLOBAL_NAV_LINKS).toHaveLength(4);

    for (const role of fullAccessRoles) {
      const links = getQCPrimaryNavLinks({ role });
      expect(links).toHaveLength(4);
      expect(links.map((link) => link.href)).toEqual(
        GLOBAL_NAV_LINKS.map((link) => link.href)
      );
    }

    for (const role of personas) {
      const links = getQCPrimaryNavLinks({ role });
      expect(links.length).toBeLessThanOrEqual(4);
    }
  });

  it("home page omits PM and automation value propositions", () => {
    const source = readHomePageSources();

    for (const term of FORBIDDEN_HOME_VALUE_TERMS) {
      expect(source).not.toContain(term);
    }
  });

  it("home page workflow mirrors QC path: report → registry → closure → portfolio", () => {
    const homePage = readSource("components/landing/PublicHomePage.tsx");

    expect(homePage).toContain("const WORKFLOW_STEPS = [");
    expect(homePage).toContain("const WORKFLOW_PILLARS = [");
    expect(homePage).toMatch(/WORKFLOW_STEPS[\s\S]*?step: "04"/);

    for (const title of QC_WORKFLOW_STEP_TITLES) {
      expect(homePage).toContain(title);
    }

    for (const value of QC_WORKFLOW_PILLAR_VALUES) {
      expect(homePage).toContain(`value: "${value}"`);
    }
  });
});
