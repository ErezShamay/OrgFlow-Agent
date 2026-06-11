import { describe, expect, it } from "vitest";

import {
  QC_PERSONAS,
  canPerformIssueTransition,
  hasQCPermission,
  qcInviteableRoles,
  resolveQCPersona,
  resolveQCPermissions,
  visibleIssueStatusesForRole,
} from "@/lib/quality-issues/permissions";

describe("qc permissions (spec 0.3)", () => {
  it("defines four QC personas", () => {
    expect(QC_PERSONAS).toEqual([
      "SUPERVISOR",
      "CONTRACTOR",
      "DEVELOPER",
      "ADMIN",
    ]);
  });

  it("maps system roles to personas including legacy roles", () => {
    expect(resolveQCPersona("SUPERVISOR")).toBe("SUPERVISOR");
    expect(resolveQCPersona("MANAGER")).toBe("SUPERVISOR");
    expect(resolveQCPersona("VIEWER")).toBe("DEVELOPER");
    expect(resolveQCPersona("PLATFORM_ADMIN")).toBe("ADMIN");
    expect(resolveQCPersona("unknown")).toBeNull();
  });

  it("grants supervisor write and verify but not user management", () => {
    const perms = resolveQCPermissions("SUPERVISOR");
    expect(perms.has("quality_issues:write")).toBe(true);
    expect(perms.has("quality_issues:verify")).toBe(true);
    expect(perms.has("users:write")).toBe(false);
  });

  it("limits contractor to remediate and filtered statuses", () => {
    expect(hasQCPermission("CONTRACTOR", "quality_issues:remediate")).toBe(
      true
    );
    expect(hasQCPermission("CONTRACTOR", "field_reports:read")).toBe(false);

    const visible = visibleIssueStatusesForRole("CONTRACTOR");
    expect(visible).not.toBeNull();
    expect(visible?.has("OPEN")).toBe(true);
    expect(visible?.has("CLOSED")).toBe(false);
  });

  it("blocks developer from status transitions", () => {
    expect(
      canPerformIssueTransition("DEVELOPER", "OPEN", "CLOSED")
    ).toBe(false);
    expect(hasQCPermission("DEVELOPER", "quality_portfolio:read")).toBe(
      true
    );
  });

  it("allows contractor remediation transition only", () => {
    expect(
      canPerformIssueTransition(
        "CONTRACTOR",
        "IN_REMEDIATION",
        "PENDING_VERIFICATION"
      )
    ).toBe(true);
    expect(
      canPerformIssueTransition("CONTRACTOR", "OPEN", "CLOSED")
    ).toBe(false);
  });

  it("lists inviteable QC roles for admins", () => {
    expect(qcInviteableRoles("ADMIN")).toContain("CONTRACTOR");
    expect(qcInviteableRoles("PLATFORM_ADMIN")).toContain("ADMIN");
    expect(qcInviteableRoles("SUPERVISOR")).toEqual([]);
  });
});
