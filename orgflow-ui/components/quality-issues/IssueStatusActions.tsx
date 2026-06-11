"use client";

import { useState } from "react";

import Button from "@/components/ui/Button";
import { updateQualityIssue } from "@/lib/quality-issues/api";
import RemediationPhotoUpload from "@/components/quality-issues/RemediationPhotoUpload";
import {
  buildRemediationUpdateRequest,
  buildReopenUpdateRequest,
  buildVerifyCloseUpdateRequest,
  canSubmitRemediation,
  getIssueStatusActions,
  type IssueStatusAction,
} from "@/lib/quality-issues/issue-status-actions";
import type { QualityIssue } from "@/lib/quality-issues/types";
import { showToast } from "@/lib/ui/toast";

type IssueStatusActionsProps = {
  issue: QualityIssue;
  role: string | null | undefined;
  onUpdated?: () => void | Promise<void>;
  className?: string;
};

export default function IssueStatusActions({
  issue,
  role,
  onUpdated,
  className = "",
}: IssueStatusActionsProps) {
  const [pendingActionId, setPendingActionId] = useState<string | null>(null);
  const [remediationNotes, setRemediationNotes] = useState("");
  const [remediationPhotoIds, setRemediationPhotoIds] = useState<string[]>([]);
  const actions = getIssueStatusActions(issue, role);
  const remediationAction = actions.find(
    (action) => action.mode === "remediation-form"
  );
  const immediateActions = actions.filter(
    (action) => action.mode === "immediate"
  );

  if (actions.length === 0) {
    return null;
  }

  async function handleImmediateAction(action: IssueStatusAction) {
    try {
      setPendingActionId(action.id);
      const request =
        action.id === "verify-close"
          ? buildVerifyCloseUpdateRequest()
          : action.id === "reopen-issue"
            ? buildReopenUpdateRequest()
            : { status: action.targetStatus };
      await updateQualityIssue(issue.id, request);
      const successMessage =
        action.id === "verify-close"
          ? "הליקוי נסגר לאחר אימות התיקון"
          : action.id === "reopen-issue"
            ? "הליקוי סומן כליקוי חוזר"
            : "סטטוס הליקוי עודכן";
      showToast(successMessage, "success");
      await onUpdated?.();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "עדכון סטטוס נכשל";
      showToast(message, "error");
    } finally {
      setPendingActionId(null);
    }
  }

  async function handleSubmitRemediation() {
    if (!remediationAction) {
      return;
    }

    try {
      setPendingActionId(remediationAction.id);
      await updateQualityIssue(
        issue.id,
        buildRemediationUpdateRequest({
          notes: remediationNotes,
          photo_ids: remediationPhotoIds,
        })
      );
      setRemediationNotes("");
      setRemediationPhotoIds([]);
      showToast("התיקון נשלח לבדיקת מפקח", "success");
      await onUpdated?.();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "שליחת התיקון נכשלה";
      showToast(message, "error");
    } finally {
      setPendingActionId(null);
    }
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {immediateActions.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {immediateActions.map((action) => (
            <Button
              key={action.id}
              type="button"
              variant="secondary"
              disabled={pendingActionId !== null}
              onClick={() => void handleImmediateAction(action)}
            >
              {pendingActionId === action.id ? "מעדכן..." : action.label}
            </Button>
          ))}
        </div>
      ) : null}

      {remediationAction ? (
        <form
          className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-900/40"
          onSubmit={(event) => {
            event.preventDefault();
            void handleSubmitRemediation();
          }}
        >
          <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
            {remediationAction.label}
          </p>
          {remediationAction.description ? (
            <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
              {remediationAction.description}
            </p>
          ) : null}
          <RemediationPhotoUpload
            issueId={issue.id}
            disabled={pendingActionId !== null}
            onPhotosChange={setRemediationPhotoIds}
            className="mt-3"
          />
          <label className="mt-3 block space-y-1.5 text-sm">
            <span className="font-medium text-zinc-700 dark:text-zinc-300">
              הערות על התיקון (אופציונלי)
            </span>
            <textarea
              className="of-input min-h-24 w-full text-base"
              value={remediationNotes}
              disabled={pendingActionId !== null}
              onChange={(event) => setRemediationNotes(event.target.value)}
              placeholder="למשל: הוחלפה ברז, בוצעה איטום מחדש"
            />
          </label>
          <div className="mt-3">
            <Button
              type="submit"
              variant="primary"
              disabled={
                pendingActionId !== null
                || !canSubmitRemediation({ photoIds: remediationPhotoIds })
              }
            >
              {pendingActionId === remediationAction.id
                ? "שולח..."
                : "שלח לבדיקת מפקח"}
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
