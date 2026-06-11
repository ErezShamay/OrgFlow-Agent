import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  contractorIssuesPageTitle,
  isContractorIssuesView,
} from "@/lib/quality-issues/contractor-issues-view";
import {
  issuesFilterStateToListQuery,
  serializeIssuesFilterKey,
} from "@/lib/quality-issues/filters";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 4.2.2 gate (contractor filtered issues view)", () => {
  it("applies OPEN/IN_REMEDIATION query defaults for contractor", () => {
    expect(isContractorIssuesView("CONTRACTOR")).toBe(true);
    expect(
      issuesFilterStateToListQuery(
        { status: "", severity: "", trade: "" },
        "CONTRACTOR"
      )
    ).toEqual({
      status: ["OPEN", "IN_REMEDIATION"],
    });
    expect(serializeIssuesFilterKey(
      { status: "", severity: "", trade: "" },
      "CONTRACTOR"
    )).toContain("contractor");
  });

  it("wires contractor issues page and banner", () => {
    const issuesPage = readSource("app/(dashboard)/issues/page.tsx");
    const projectIssuesPage = readSource(
      "app/(dashboard)/projects/[id]/issues/page.tsx"
    );
    const banner = readSource(
      "components/quality-issues/ContractorIssuesBanner.tsx"
    );

    expect(issuesPage).toContain("ContractorIssuesBanner");
    expect(issuesPage).toContain("listOrganizationQualityIssues");
    expect(issuesPage).toContain("contractorIssuesPageTitle");
    expect(projectIssuesPage).toContain("ContractorIssuesBanner");
    expect(banner).toContain("תצוגת קבלן");
    expect(banner).toContain("VISIBLE_STATUS_LABELS");
  });
});
