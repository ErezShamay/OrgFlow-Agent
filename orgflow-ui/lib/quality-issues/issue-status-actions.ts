import {
  canPerformIssueTransition,
  resolveQCPersona,
} from "@/lib/quality-issues/permissions";
import type { QualityIssue, QualityIssueStatus } from "@/lib/quality-issues/types";

export type IssueStatusActionId =
  | "start-remediation"
  | "submit-remediation"
  | "verify-close"
  | "reopen-issue";

export type IssueStatusActionMode = "immediate" | "remediation-form";

export type IssueStatusAction = {
  id: IssueStatusActionId;
  label: string;
  targetStatus: QualityIssueStatus;
  description?: string;
  mode: IssueStatusActionMode;
};

export type SubmitRemediationInput = {
  notes?: string | null;
  photo_ids?: string[];
};

export function buildVerifyCloseUpdateRequest(): {
  status: "CLOSED";
} {
  return { status: "CLOSED" };
}

export function buildReopenUpdateRequest(): {
  status: "REOPENED";
} {
  return { status: "REOPENED" };
}

export function canSubmitRemediation(input: {
  photoIds: string[];
}): boolean {
  return input.photoIds.length > 0;
}

export function buildRemediationUpdateRequest(
  input: SubmitRemediationInput = {}
): {
  status: "PENDING_VERIFICATION";
  notes?: string;
  photo_ids?: string[];
} {
  const request: {
    status: "PENDING_VERIFICATION";
    notes?: string;
    photo_ids?: string[];
  } = {
    status: "PENDING_VERIFICATION",
  };

  const notes = input.notes?.trim();
  if (notes) {
    request.notes = notes;
  }

  if (input.photo_ids?.length) {
    request.photo_ids = input.photo_ids;
  }

  return request;
}

export function getIssueStatusActions(
  issue: Pick<QualityIssue, "status">,
  role: string | null | undefined
): IssueStatusAction[] {
  const actions: IssueStatusAction[] = [];
  const persona = resolveQCPersona(role);

  if (
    issue.status === "OPEN" &&
    canPerformIssueTransition(role, "OPEN", "IN_REMEDIATION")
  ) {
    actions.push({
      id: "start-remediation",
      label: "סמן בטיפול",
      targetStatus: "IN_REMEDIATION",
      description: "העברת הליקוי לקבלן לטיפול",
      mode: "immediate",
    });
  }

  if (
    issue.status === "IN_REMEDIATION" &&
    persona === "CONTRACTOR" &&
    canPerformIssueTransition(
      role,
      "IN_REMEDIATION",
      "PENDING_VERIFICATION"
    )
  ) {
    actions.push({
      id: "submit-remediation",
      label: "הגש תיקון לבדיקה",
      targetStatus: "PENDING_VERIFICATION",
      description: "שליחה למפקח לאימות לאחר ביצוע התיקון",
      mode: "remediation-form",
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
      description: "אימות התיקון וסגירת הליקוי לאחר בדיקה בשטח",
      mode: "immediate",
    });
  }

  if (
    issue.status === "CLOSED" &&
    canPerformIssueTransition(role, "CLOSED", "REOPENED")
  ) {
    actions.push({
      id: "reopen-issue",
      label: "סמן כחוזר",
      targetStatus: "REOPENED",
      description: "הליקוי הסגור הופיע שוב בשטח - מונה חזרות יעלה",
      mode: "immediate",
    });
  }

  return actions;
}
