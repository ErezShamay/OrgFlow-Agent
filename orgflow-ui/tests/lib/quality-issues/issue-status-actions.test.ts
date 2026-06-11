import { describe, expect, it } from "vitest";

import {
  buildRemediationUpdateRequest,
  buildReopenUpdateRequest,
  buildVerifyCloseUpdateRequest,
  getIssueStatusActions,
} from "@/lib/quality-issues/issue-status-actions";
import type { QualityIssue } from "@/lib/quality-issues/types";

const OPEN_ISSUE: Pick<QualityIssue, "status"> = {
  status: "OPEN",
};

const IN_REMEDIATION_ISSUE: Pick<QualityIssue, "status"> = {
  status: "IN_REMEDIATION",
};

const PENDING_VERIFICATION_ISSUE: Pick<QualityIssue, "status"> = {
  status: "PENDING_VERIFICATION",
};

const CLOSED_ISSUE: Pick<QualityIssue, "status"> = {
  status: "CLOSED",
};

describe("issue status actions (2.2.1–2.2.4)", () => {
  it("offers start-remediation for supervisor on open issues", () => {
    const actions = getIssueStatusActions(OPEN_ISSUE, "SUPERVISOR");

    expect(actions).toEqual([
      {
        id: "start-remediation",
        label: "סמן בטיפול",
        targetStatus: "IN_REMEDIATION",
        description: "העברת הליקוי לקבלן לטיפול",
        mode: "immediate",
      },
    ]);
  });

  it("offers start-remediation for admin on open issues", () => {
    expect(getIssueStatusActions(OPEN_ISSUE, "ADMIN")).toHaveLength(1);
  });

  it("does not offer actions for developer or contractor on open issues", () => {
    expect(getIssueStatusActions(OPEN_ISSUE, "DEVELOPER")).toEqual([]);
    expect(getIssueStatusActions(OPEN_ISSUE, "CONTRACTOR")).toEqual([]);
  });

  it("does not offer start-remediation when issue is already in remediation", () => {
    expect(
      getIssueStatusActions(IN_REMEDIATION_ISSUE, "SUPERVISOR")
    ).toEqual([]);
  });

  it("offers submit-remediation form for contractor on in-remediation issues", () => {
    const actions = getIssueStatusActions(IN_REMEDIATION_ISSUE, "CONTRACTOR");

    expect(actions).toEqual([
      {
        id: "submit-remediation",
        label: "הגש תיקון לבדיקה",
        targetStatus: "PENDING_VERIFICATION",
        description: "שליחה למפקח לאימות לאחר ביצוע התיקון",
        mode: "remediation-form",
      },
    ]);
  });

  it("does not offer submit-remediation to supervisor or developer", () => {
    expect(getIssueStatusActions(IN_REMEDIATION_ISSUE, "SUPERVISOR")).toEqual(
      []
    );
    expect(getIssueStatusActions(IN_REMEDIATION_ISSUE, "DEVELOPER")).toEqual([]);
  });

  it("builds remediation update request with optional notes and photos", () => {
    expect(buildRemediationUpdateRequest()).toEqual({
      status: "PENDING_VERIFICATION",
    });
    expect(
      buildRemediationUpdateRequest({ notes: "  הוחלפה ברז  " })
    ).toEqual({
      status: "PENDING_VERIFICATION",
      notes: "הוחלפה ברז",
    });
    expect(
      buildRemediationUpdateRequest({
        photo_ids: ["photo-1"],
      })
    ).toEqual({
      status: "PENDING_VERIFICATION",
      photo_ids: ["photo-1"],
    });
  });

  it("offers verify-close for supervisor on pending-verification issues", () => {
    const actions = getIssueStatusActions(
      PENDING_VERIFICATION_ISSUE,
      "SUPERVISOR"
    );

    expect(actions).toEqual([
      {
        id: "verify-close",
        label: "אשר סגירה",
        targetStatus: "CLOSED",
        description: "אימות התיקון וסגירת הליקוי לאחר בדיקה בשטח",
        mode: "immediate",
      },
    ]);
  });

  it("offers verify-close for admin on pending-verification issues", () => {
    expect(
      getIssueStatusActions(PENDING_VERIFICATION_ISSUE, "ADMIN")
    ).toHaveLength(1);
  });

  it("does not offer verify-close to contractor or developer", () => {
    expect(
      getIssueStatusActions(PENDING_VERIFICATION_ISSUE, "CONTRACTOR")
    ).toEqual([]);
    expect(
      getIssueStatusActions(PENDING_VERIFICATION_ISSUE, "DEVELOPER")
    ).toEqual([]);
  });

  it("builds verify-close update request", () => {
    expect(buildVerifyCloseUpdateRequest()).toEqual({
      status: "CLOSED",
    });
  });

  it("offers reopen-issue for supervisor on closed issues", () => {
    const actions = getIssueStatusActions(CLOSED_ISSUE, "SUPERVISOR");

    expect(actions).toEqual([
      {
        id: "reopen-issue",
        label: "סמן כחוזר",
        targetStatus: "REOPENED",
        description: "הליקוי הסגור הופיע שוב בשטח - מונה חזרות יעלה",
        mode: "immediate",
      },
    ]);
  });

  it("offers reopen-issue for admin on closed issues", () => {
    expect(getIssueStatusActions(CLOSED_ISSUE, "ADMIN")).toHaveLength(1);
  });

  it("does not offer reopen-issue to contractor or developer", () => {
    expect(getIssueStatusActions(CLOSED_ISSUE, "CONTRACTOR")).toEqual([]);
    expect(getIssueStatusActions(CLOSED_ISSUE, "DEVELOPER")).toEqual([]);
  });

  it("builds reopen update request", () => {
    expect(buildReopenUpdateRequest()).toEqual({
      status: "REOPENED",
    });
  });
});
