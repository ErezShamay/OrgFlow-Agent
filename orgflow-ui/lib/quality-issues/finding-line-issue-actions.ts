import {
  buildReopenUpdateRequest,
  buildVerifyCloseUpdateRequest,
} from "@/lib/quality-issues/issue-status-actions";
import { canPerformIssueTransition } from "@/lib/quality-issues/permissions";
import type {
  QualityIssue,
  QualityIssueStatus,
  QualityIssueUpdateRequest,
} from "@/lib/quality-issues/types";

export type FindingLineIssueActionId =
  | "mark-closed"
  | "verify-close"
  | "reopen-issue";

export type FindingLineIssueAction = {
  id: FindingLineIssueActionId;
  label: string;
  targetStatus: QualityIssueStatus;
  description?: string;
};

export function getFindingLineIssueStatusActions(
  issue: Pick<QualityIssue, "status">,
  role: string | null | undefined
): FindingLineIssueAction[] {
  const actions: FindingLineIssueAction[] = [];

  if (
    (issue.status === "OPEN" || issue.status === "REOPENED") &&
    canPerformIssueTransition(role, issue.status, "CLOSED")
  ) {
    actions.push({
      id: "mark-closed",
      label: "סמן כנסגר",
      targetStatus: "CLOSED",
      description: "התיקון אומת בביקור - סגירת הליקוי",
    });
  }

  if (
    issue.status === "PENDING_VERIFICATION" &&
    canPerformIssueTransition(role, "PENDING_VERIFICATION", "CLOSED")
  ) {
    actions.push({
      id: "verify-close",
      label: "אשר סגירה",
      targetStatus: "CLOSED",
      description: "אימות התיקון וסגירת הליקוי",
    });
  }

  if (
    issue.status === "CLOSED" &&
    canPerformIssueTransition(role, "CLOSED", "REOPENED")
  ) {
    actions.push({
      id: "reopen-issue",
      label: "חזר",
      targetStatus: "REOPENED",
      description: "הליקוי הסגור הופיע שוב בביקור זה",
    });
  }

  return actions;
}

export function buildFindingLineIssueUpdateRequest(
  action: FindingLineIssueAction,
  context: {
    reportId?: string | null;
    lineId?: string | null;
  } = {}
): QualityIssueUpdateRequest {
  const base =
    action.id === "reopen-issue"
      ? buildReopenUpdateRequest()
      : buildVerifyCloseUpdateRequest();

  const request: QualityIssueUpdateRequest = { ...base };

  if (context.reportId?.trim()) {
    request.last_seen_report_id = context.reportId.trim();
  }

  if (context.lineId?.trim()) {
    request.last_seen_line_id = context.lineId.trim();
  }

  return request;
}

export function findingLineIssueActionSuccessMessage(
  actionId: FindingLineIssueActionId
): string {
  switch (actionId) {
    case "mark-closed":
      return "הליקוי סומן כנסגר";
    case "verify-close":
      return "הליקוי נסגר לאחר אימות";
    case "reopen-issue":
      return "הליקוי סומן כחוזר";
    default:
      return "סטטוס הליקוי עודכן";
  }
}
