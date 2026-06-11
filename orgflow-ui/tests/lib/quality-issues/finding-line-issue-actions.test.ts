import { describe, expect, it } from "vitest";

import {
  buildFindingLineIssueUpdateRequest,
  findingLineIssueActionSuccessMessage,
  getFindingLineIssueStatusActions,
} from "@/lib/quality-issues/finding-line-issue-actions";
import type { QualityIssue } from "@/lib/quality-issues/types";

const OPEN_ISSUE: Pick<QualityIssue, "status"> = { status: "OPEN" };
const PENDING_ISSUE: Pick<QualityIssue, "status"> = {
  status: "PENDING_VERIFICATION",
};
const CLOSED_ISSUE: Pick<QualityIssue, "status"> = { status: "CLOSED" };
const REOPENED_ISSUE: Pick<QualityIssue, "status"> = { status: "REOPENED" };

describe("finding line issue actions (2.2.6)", () => {
  it("offers mark-closed for supervisor on open issues", () => {
    expect(getFindingLineIssueStatusActions(OPEN_ISSUE, "SUPERVISOR")).toEqual([
      {
        id: "mark-closed",
        label: "סמן כנסגר",
        targetStatus: "CLOSED",
        description: "התיקון אומת בביקור - סגירת הליקוי",
      },
    ]);
  });

  it("offers mark-closed for supervisor on reopened issues", () => {
    expect(
      getFindingLineIssueStatusActions(REOPENED_ISSUE, "SUPERVISOR")
    ).toHaveLength(1);
    expect(
      getFindingLineIssueStatusActions(REOPENED_ISSUE, "SUPERVISOR")[0]?.label
    ).toBe("סמן כנסגר");
  });

  it("offers verify-close for supervisor on pending verification", () => {
    expect(
      getFindingLineIssueStatusActions(PENDING_ISSUE, "SUPERVISOR")
    ).toEqual([
      {
        id: "verify-close",
        label: "אשר סגירה",
        targetStatus: "CLOSED",
        description: "אימות התיקון וסגירת הליקוי",
      },
    ]);
  });

  it("offers reopen for supervisor on closed issues", () => {
    expect(getFindingLineIssueStatusActions(CLOSED_ISSUE, "SUPERVISOR")).toEqual(
      [
        {
          id: "reopen-issue",
          label: "חזר",
          targetStatus: "REOPENED",
          description: "הליקוי הסגור הופיע שוב בביקור זה",
        },
      ]
    );
  });

  it("does not offer actions to contractor", () => {
    expect(getFindingLineIssueStatusActions(OPEN_ISSUE, "CONTRACTOR")).toEqual(
      []
    );
    expect(
      getFindingLineIssueStatusActions(PENDING_ISSUE, "CONTRACTOR")
    ).toEqual([]);
    expect(
      getFindingLineIssueStatusActions(CLOSED_ISSUE, "CONTRACTOR")
    ).toEqual([]);
  });

  it("builds update request with report and line context", () => {
    const action = getFindingLineIssueStatusActions(
      OPEN_ISSUE,
      "SUPERVISOR"
    )[0]!;

    expect(
      buildFindingLineIssueUpdateRequest(action, {
        reportId: "report-1",
        lineId: "line-1",
      })
    ).toEqual({
      status: "CLOSED",
      last_seen_report_id: "report-1",
      last_seen_line_id: "line-1",
    });
  });

  it("maps success messages for visit-line actions", () => {
    expect(findingLineIssueActionSuccessMessage("mark-closed")).toBe(
      "הליקוי סומן כנסגר"
    );
    expect(findingLineIssueActionSuccessMessage("verify-close")).toBe(
      "הליקוי נסגר לאחר אימות"
    );
    expect(findingLineIssueActionSuccessMessage("reopen-issue")).toBe(
      "הליקוי סומן כחוזר"
    );
  });
});
