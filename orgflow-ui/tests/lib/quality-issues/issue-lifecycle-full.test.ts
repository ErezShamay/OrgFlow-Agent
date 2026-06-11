import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  buildFindingLineIssueUpdateRequest,
  getFindingLineIssueStatusActions,
} from "@/lib/quality-issues/finding-line-issue-actions";
import {
  buildRemediationUpdateRequest,
  buildReopenUpdateRequest,
  buildVerifyCloseUpdateRequest,
  getIssueStatusActions,
} from "@/lib/quality-issues/issue-status-actions";
import { LIFECYCLE_CLOSURE_EVENT_TYPES } from "@/lib/quality-issues/issue-detail";
import type {
  QualityIssue,
  QualityIssueStatus,
  QualityIssueUpdateRequest,
} from "@/lib/quality-issues/types";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

type LifecycleStep = {
  status: QualityIssueStatus;
  actorRole: string;
  actionId: string;
  buildRequest: () => QualityIssueUpdateRequest;
};

function applyLifecycleStep(
  issue: Pick<QualityIssue, "status">,
  step: LifecycleStep
): QualityIssueStatus {
  const detailActions = getIssueStatusActions(issue, step.actorRole);
  const detailAction = detailActions.find((action) => action.id === step.actionId);
  expect(detailAction, `missing detail action ${step.actionId}`).toBeDefined();
  expect(detailAction?.targetStatus).toBe(step.buildRequest().status);

  return step.buildRequest().status as QualityIssueStatus;
}

describe("issue lifecycle full (2.2.7)", () => {
  it("walks remediation lifecycle with correct actions per role", () => {
    let issue: Pick<QualityIssue, "status"> = { status: "OPEN" };

    const steps: LifecycleStep[] = [
      {
        status: "OPEN",
        actorRole: "SUPERVISOR",
        actionId: "start-remediation",
        buildRequest: () => ({ status: "IN_REMEDIATION" }),
      },
      {
        status: "IN_REMEDIATION",
        actorRole: "CONTRACTOR",
        actionId: "submit-remediation",
        buildRequest: () =>
          buildRemediationUpdateRequest({
            notes: "הוחלפה ברז",
            photo_ids: ["photo-1"],
          }),
      },
      {
        status: "PENDING_VERIFICATION",
        actorRole: "SUPERVISOR",
        actionId: "verify-close",
        buildRequest: buildVerifyCloseUpdateRequest,
      },
      {
        status: "CLOSED",
        actorRole: "SUPERVISOR",
        actionId: "reopen-issue",
        buildRequest: buildReopenUpdateRequest,
      },
    ];

    for (const step of steps) {
      expect(issue.status).toBe(step.status);
      issue = {
        status: applyLifecycleStep(issue, step),
      };
    }

    expect(issue.status).toBe("REOPENED");
    expect(getIssueStatusActions(issue, "CONTRACTOR")).toEqual([]);
    expect(getIssueStatusActions(issue, "DEVELOPER")).toEqual([]);
  });

  it("supports visit-line direct close and reopen on second visit", () => {
    const reopenedIssue: Pick<QualityIssue, "status"> = { status: "REOPENED" };

    const closeAction = getFindingLineIssueStatusActions(
      reopenedIssue,
      "SUPERVISOR"
    )[0];
    expect(closeAction?.id).toBe("mark-closed");

    const closeRequest = buildFindingLineIssueUpdateRequest(closeAction!, {
      reportId: "report-2",
      lineId: "line-2",
    });
    expect(closeRequest).toEqual({
      status: "CLOSED",
      last_seen_report_id: "report-2",
      last_seen_line_id: "line-2",
    });

    const closedIssue: Pick<QualityIssue, "status"> = { status: "CLOSED" };
    const reopenAction = getFindingLineIssueStatusActions(
      closedIssue,
      "SUPERVISOR"
    )[0];
    expect(reopenAction?.id).toBe("reopen-issue");
    expect(buildFindingLineIssueUpdateRequest(reopenAction!, {
      reportId: "report-3",
      lineId: "line-3",
    })).toEqual({
      status: "REOPENED",
      last_seen_report_id: "report-3",
      last_seen_line_id: "line-3",
    });
  });

  it("tracks closure lifecycle event types for timeline rendering", () => {
    expect(LIFECYCLE_CLOSURE_EVENT_TYPES.has("REMEDIATION_SUBMITTED")).toBe(
      true
    );
    expect(LIFECYCLE_CLOSURE_EVENT_TYPES.has("VERIFIED_CLOSED")).toBe(true);
    expect(LIFECYCLE_CLOSURE_EVENT_TYPES.has("REOPENED")).toBe(true);
    expect(LIFECYCLE_CLOSURE_EVENT_TYPES.has("DETECTED")).toBe(false);
  });
});

describe("issue lifecycle full UI gate (2.2.7)", () => {
  it("wires full lifecycle actions across issue detail and finding rows", () => {
    const detailPanel = readUiSource(
      "components/quality-issues/IssueDetailPanel.tsx"
    );
    const statusActions = readUiSource(
      "components/quality-issues/IssueStatusActions.tsx"
    );
    const findingActions = readUiSource(
      "components/quality-issues/FindingLinkedIssueStatusActions.tsx"
    );
    const timeline = readUiSource(
      "components/quality-issues/IssueEventsTimeline.tsx"
    );
    const detailHelpers = readUiSource("lib/quality-issues/issue-detail.ts");
    const statusHelpers = readUiSource(
      "lib/quality-issues/issue-status-actions.ts"
    );
    const findingHelpers = readUiSource(
      "lib/quality-issues/finding-line-issue-actions.ts"
    );

    expect(detailPanel).toContain("IssueStatusActions");
    expect(detailPanel).toContain("IssueEventsTimeline");
    expect(statusActions).toContain("buildRemediationUpdateRequest");
    expect(statusActions).toContain("buildVerifyCloseUpdateRequest");
    expect(statusActions).toContain("buildReopenUpdateRequest");
    expect(findingActions).toContain("getFindingLineIssueStatusActions");
    expect(findingActions).toContain("buildFindingLineIssueUpdateRequest");
    expect(timeline).toContain("formatQualityIssueEventDetails");
    expect(detailHelpers).toContain("LIFECYCLE_CLOSURE_EVENT_TYPES");
    expect(statusHelpers).toContain("סמן בטיפול");
    expect(statusHelpers).toContain("אשר סגירה");
    expect(statusHelpers).toContain("סמן כחוזר");
    expect(findingHelpers).toContain("סמן כנסגר");
    expect(findingHelpers).toContain("חזר");
  });
});
