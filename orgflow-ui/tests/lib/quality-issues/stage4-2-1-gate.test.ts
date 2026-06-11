import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { inviteableRoles } from "@/lib/auth/permissions";
import { contractorHasLimitedAccess } from "@/lib/auth/contractor-access";
import { getRoleLabel } from "@/lib/auth/roleLabels";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("stage 4.2.1 gate (CONTRACTOR role + limited permissions)", () => {
  it("wires contractor into invite UI and access helpers", () => {
    const usersPage = readSource("app/(dashboard)/admin/users/page.tsx");
    const contractorAccess = readSource("lib/auth/contractor-access.ts");

    expect(inviteableRoles("ADMIN")).toContain("CONTRACTOR");
    expect(contractorHasLimitedAccess("CONTRACTOR")).toBe(true);
    expect(getRoleLabel("CONTRACTOR")).toBe("קבלן");
    expect(usersPage).toContain("CONTRACTOR");
    expect(contractorAccess).toContain("CONTRACTOR_DENIED_PERMISSIONS");
  });
});
