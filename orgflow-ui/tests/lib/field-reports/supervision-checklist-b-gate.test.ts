/**
 * Gate — שלב B (field-supervision-checklist-spec §16.B).
 * סיווג תוכן קטלוג: scope / public_area_id + buildSupervisionChecklist לא ריק.
 */
import { execSync } from "node:child_process";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { buildSupervisionChecklist } from "@/lib/field-reports/supervision-checklist-builder";
import type {
  PublicAreaId,
  SupervisionCatalog,
} from "@/lib/field-reports/schema/types";
import { PUBLIC_AREA_DEFINITIONS } from "@/lib/field-reports/schema/types";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

const PUBLIC_AREA_IDS = PUBLIC_AREA_DEFINITIONS.map((area) => area.id);

function loadSupervisionCatalogFromSeed(): SupervisionCatalog {
  const output = execSync(
    `python3 -c "
import json
from app.config.field_report_catalog_supervision_seed import (
    SUPERVISION_CATALOG_ISSUES,
    SUPERVISION_CATALOG_VERSION,
)
issues = []
for issue in SUPERVISION_CATALOG_ISSUES:
    issues.append({
        'issue_id': issue['issue_id'],
        'issue_name_he': issue['issue_name_he'],
        'standard_ref': issue['standard_ref'],
        'top_family': issue['top_family'],
        'category_id': issue['category_id'],
        'category_name_he': issue['category_name_he'],
        'severity': issue.get('severity'),
        'scope': issue['scope'],
        'public_area_id': issue.get('public_area_id'),
        'allowed_stages': list(issue['allowed_stages']),
    })
print(json.dumps({'catalog_version': SUPERVISION_CATALOG_VERSION, 'issues': issues}))
"`,
    { cwd: REPO_ROOT, encoding: "utf8" }
  );

  return JSON.parse(output.trim()) as SupervisionCatalog;
}

describe("supervision checklist stage B gate (§16.B)", () => {
  const catalog = loadSupervisionCatalogFromSeed();

  it("every issue has scope, standard_ref, allowed_stages (inline, no defaults layer)", () => {
    expect(catalog.issues.length).toBeGreaterThanOrEqual(30);

    for (const issue of catalog.issues) {
      expect(issue.standard_ref, issue.issue_id).toBeTruthy();
      expect(issue.scope, issue.issue_id).toMatch(
        /^(APARTMENT|PUBLIC_AREA|BOTH)$/
      );
      expect(issue.allowed_stages?.length, issue.issue_id).toBeGreaterThan(0);
    }
  });

  it("no PUBLIC_AREA item without public_area_id", () => {
    const orphans = catalog.issues.filter(
      (issue) => issue.scope === "PUBLIC_AREA" && !issue.public_area_id
    );

    expect(orphans.map((issue) => issue.issue_id)).toEqual([]);
  });

  it("each public area has at least 3 PUBLIC_AREA-scoped items with matching public_area_id", () => {
    const counts = Object.fromEntries(
      PUBLIC_AREA_IDS.map((id) => [id, 0])
    ) as Record<PublicAreaId, number>;

    for (const issue of catalog.issues) {
      if (
        issue.scope === "PUBLIC_AREA" &&
        issue.public_area_id &&
        issue.public_area_id in counts
      ) {
        counts[issue.public_area_id as PublicAreaId] += 1;
      }
    }

    for (const areaId of PUBLIC_AREA_IDS) {
      expect(counts[areaId], areaId).toBeGreaterThanOrEqual(3);
    }
  });

  it("buildSupervisionChecklist returns non-empty items for apartment STRUCTURE and FINISHING", () => {
    const structure = buildSupervisionChecklist({
      catalog,
      constructionStage: "STRUCTURE",
      visitScope: "APARTMENT",
      apartmentNumber: "5",
    });

    expect(structure.items.length).toBeGreaterThan(0);

    const finishing = buildSupervisionChecklist({
      catalog,
      constructionStage: "FINISHING",
      visitScope: "APARTMENT",
      apartmentNumber: "5",
    });

    expect(finishing.items.length).toBeGreaterThan(0);
  });

  it("buildSupervisionChecklist returns non-empty items for every public area (FINISHING)", () => {
    for (const area of PUBLIC_AREA_DEFINITIONS) {
      const block = buildSupervisionChecklist({
        catalog,
        constructionStage: "FINISHING",
        visitScope: "PUBLIC_AREA",
        publicAreaId: area.id,
      });

      expect(block.items.length, area.id).toBeGreaterThan(0);
      expect(
        block.items.some(
          (item) =>
            catalog.issues.find((i) => i.issue_id === item.catalog_issue_id)
              ?.public_area_id === area.id
        ),
        area.id
      ).toBe(true);
    }
  });
});
