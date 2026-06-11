import { describe, expect, it } from "vitest";

import {
  canContractorAccessRoute,
  contractorDeniedRouteRedirect,
  isContractorDeniedRoute,
} from "@/lib/auth/contractor-route-guard";

describe("contractor route guard (4.2.4)", () => {
  it("blocks field reports, portfolio, and catalog-related PM routes", () => {
    expect(isContractorDeniedRoute("/field-reports")).toBe(true);
    expect(isContractorDeniedRoute("/field-reports/report-1")).toBe(true);
    expect(isContractorDeniedRoute("/portfolio")).toBe(true);
    expect(isContractorDeniedRoute("/upload")).toBe(true);
    expect(isContractorDeniedRoute("/reviews")).toBe(true);
    expect(isContractorDeniedRoute("/projects/proj-1/field-reports")).toBe(
      true
    );
    expect(isContractorDeniedRoute("/projects/proj-1/reviews")).toBe(true);
  });

  it("allows contractor issues and project overview routes", () => {
    expect(isContractorDeniedRoute("/issues")).toBe(false);
    expect(isContractorDeniedRoute("/issues/issue-1")).toBe(false);
    expect(isContractorDeniedRoute("/projects")).toBe(false);
    expect(isContractorDeniedRoute("/projects/proj-1")).toBe(false);
    expect(isContractorDeniedRoute("/projects/proj-1/issues")).toBe(false);
    expect(isContractorDeniedRoute("/settings")).toBe(false);
  });

  it("evaluates access by role and redirects to issues home", () => {
    expect(canContractorAccessRoute("CONTRACTOR", "/field-reports")).toBe(
      false
    );
    expect(canContractorAccessRoute("CONTRACTOR", "/issues")).toBe(true);
    expect(canContractorAccessRoute("SUPERVISOR", "/field-reports")).toBe(true);
    expect(contractorDeniedRouteRedirect("CONTRACTOR")).toBe("/issues");
  });
});
