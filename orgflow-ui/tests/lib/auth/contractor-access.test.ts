import { describe, expect, it } from "vitest";

import {
  CONTRACTOR_DENIED_PERMISSIONS,
  CONTRACTOR_GRANTED_PERMISSIONS,
  contractorHasLimitedAccess,
  getContractorAccessProfile,
  isContractorRole,
} from "@/lib/auth/contractor-access";
import { inviteableRoles } from "@/lib/auth/permissions";
import { getRoleDescription, getRoleLabel } from "@/lib/auth/roleLabels";

describe("contractor access profile (stage 4.2.1)", () => {
  it("identifies contractor role and limited permissions", () => {
    expect(isContractorRole("CONTRACTOR")).toBe(true);
    expect(contractorHasLimitedAccess("CONTRACTOR")).toBe(true);

    const profile = getContractorAccessProfile("CONTRACTOR");
    for (const permission of CONTRACTOR_GRANTED_PERMISSIONS) {
      expect(profile.permissions).toContain(permission);
    }
    for (const permission of CONTRACTOR_DENIED_PERMISSIONS) {
      expect(profile.permissions).not.toContain(permission);
    }
    expect(profile.canAccessFieldReports).toBe(false);
    expect(profile.canAccessPortfolio).toBe(false);
    expect(profile.visibleIssueStatuses).toEqual(["OPEN", "IN_REMEDIATION"]);
  });

  it("exposes contractor in admin invite roles and labels", () => {
    expect(inviteableRoles("ADMIN")).toContain("CONTRACTOR");
    expect(inviteableRoles("PLATFORM_ADMIN")).toContain("CONTRACTOR");
    expect(getRoleLabel("CONTRACTOR")).toBe("קבלן");
    expect(getRoleDescription("CONTRACTOR")).toContain("ליקויים");
  });
});
