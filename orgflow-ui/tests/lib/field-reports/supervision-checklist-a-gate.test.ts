/**
 * Gate — שלב A (field-supervision-checklist-spec §16.A).
 * סכימה + קטלוג v1.4 עם scope / allowed_stages + types + builder.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { execPythonScript } from "../../helpers/python-command";

const UI_ROOT = path.resolve(__dirname, "../../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

function readSource(root: string, relativePath: string): string {
  return readFileSync(path.join(root, relativePath), "utf8");
}

describe("supervision checklist stage A gate (§16.A)", () => {
  it("catalog v1.4 — every issue has scope, standard_ref, allowed_stages", () => {
    const output = execPythonScript(
      `
from app.config.field_report_catalog_supervision_seed import (
    SUPERVISION_CATALOG_ISSUES,
    SUPERVISION_CATALOG_VERSION,
)
assert SUPERVISION_CATALOG_VERSION == '1.4.0-supervision-checklist', SUPERVISION_CATALOG_VERSION
assert len(SUPERVISION_CATALOG_ISSUES) >= 30
for issue in SUPERVISION_CATALOG_ISSUES:
    assert issue.get('standard_ref'), issue['issue_id']
    assert issue.get('scope') in ('APARTMENT', 'PUBLIC_AREA', 'BOTH'), issue['issue_id']
    assert issue.get('allowed_stages'), issue['issue_id']
print('ok', len(SUPERVISION_CATALOG_ISSUES))
`,
      { cwd: REPO_ROOT, encoding: "utf8" }
    );

    expect(output).toContain("ok");
  });

  it("types.ts defines supervision_checklist without breaking legacy checklist", () => {
    const types = readSource(
      UI_ROOT,
      "lib/field-reports/schema/types.ts"
    );

    expect(types).toContain('kind: "supervision_checklist"');
    expect(types).toContain("SupervisionChecklistItem");
    expect(types).toContain("SupervisionReportMeta");
    expect(types).toContain('kind: "checklist"');
    expect(types).toContain("ChecklistItemStatus");
    expect(types).toContain("PUBLIC_AREA_DEFINITIONS");
  });

  it("normalize.ts handles supervision_checklist block kind", () => {
    const normalize = readSource(
      UI_ROOT,
      "lib/field-reports/schema/normalize.ts"
    );

    expect(normalize).toContain('case "supervision_checklist"');
    expect(normalize).toContain("normalizeSupervisionChecklistBlock");
    expect(normalize).toContain("normalizeSupervisionMeta");
  });

  it("supervision-checklist-builder.ts exists with buildSupervisionChecklist", () => {
    const builder = readSource(
      UI_ROOT,
      "lib/field-reports/supervision-checklist-builder.ts"
    );

    expect(builder).toContain("export function buildSupervisionChecklist");
    expect(builder).toContain("filterSupervisionCatalogIssues");
    expect(builder).toContain("isSupervisionChecklistReport");
  });
});
