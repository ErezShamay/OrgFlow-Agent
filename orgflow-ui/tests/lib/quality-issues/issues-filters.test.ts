import { describe, expect, it } from "vitest";

import {
  availableStatusFilterOptions,
  createEmptyIssuesFilterState,
  hasActiveIssuesFilters,
  issuesFilterStateToListQuery,
  serializeIssuesFilterKey,
} from "@/lib/quality-issues/filters";

describe("quality issue filters (1.3.5)", () => {
  it("starts with empty filter state", () => {
    expect(createEmptyIssuesFilterState()).toEqual({
      status: "",
      severity: "",
      trade: "",
    });
    expect(hasActiveIssuesFilters(createEmptyIssuesFilterState())).toBe(false);
  });

  it("maps filter state to API list query", () => {
    expect(
      issuesFilterStateToListQuery({
        status: "OPEN",
        severity: "CRITICAL",
        trade: "  אינסטלציה ",
      })
    ).toEqual({
      status: ["OPEN"],
      severity: ["CRITICAL"],
      trade: "אינסטלציה",
    });

    expect(
      issuesFilterStateToListQuery(createEmptyIssuesFilterState())
    ).toEqual({});
  });

  it("serializes filter key for query cache", () => {
    expect(
      serializeIssuesFilterKey({
        status: "OPEN",
        severity: "",
        trade: "טיח",
      })
    ).toBe("all|all-statuses|OPEN|_|טיח");
  });

  it("limits contractor status options to visible statuses", () => {
    const options = availableStatusFilterOptions("CONTRACTOR");
    expect(options).toEqual(["OPEN", "IN_REMEDIATION"]);
    expect(availableStatusFilterOptions("SUPERVISOR").length).toBe(5);
  });

  it("applies contractor default status filter in list query", () => {
    expect(
      issuesFilterStateToListQuery(createEmptyIssuesFilterState(), "CONTRACTOR")
    ).toEqual({
      status: ["OPEN", "IN_REMEDIATION"],
    });
    expect(
      serializeIssuesFilterKey(createEmptyIssuesFilterState(), "CONTRACTOR")
    ).toContain("contractor");
  });

  it("detects active filters", () => {
    expect(
      hasActiveIssuesFilters({
        status: "",
        severity: "HIGH",
        trade: "",
      })
    ).toBe(true);
    expect(
      hasActiveIssuesFilters({
        status: "",
        severity: "",
        trade: "   ",
      })
    ).toBe(false);
  });
});
