"use client";

import { useCallback, useEffect, useState } from "react";

import { severityBadgeVariant } from "@/components/quality-issues/IssuesTable";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { useOffline } from "@/providers/OfflineProvider";
import { updateQualityIssue } from "@/lib/quality-issues/api";
import {
  buildFindingLineIssueUpdateRequest,
  findingLineIssueActionSuccessMessage,
  getFindingLineIssueStatusActions,
  type FindingLineIssueAction,
} from "@/lib/quality-issues/finding-line-issue-actions";
import { patchOpenIssuesCacheAfterIssueUpdate } from "@/lib/quality-issues/open-issues-offline";
import { hasQCPermission } from "@/lib/quality-issues/permissions";
import { resolveLinkedIssueForFindingLine } from "@/lib/quality-issues/resolve-linked-issue-for-finding-line";
import {
  QUALITY_ISSUE_SEVERITY_LABELS_HE,
  QUALITY_ISSUE_STATUS_LABELS_HE,
  type QualityIssue,
  type QualityIssueSeverity,
} from "@/lib/quality-issues/types";
import { FR_TOUCH_BUTTON } from "@/lib/field-reports/touch-input-class";
import { showToast } from "@/lib/ui/toast";

type FindingLinkedIssueStatusActionsProps = {
  projectId: string;
  organizationId?: string | null;
  linkedIssueId: string;
  reportId?: string | null;
  lineId?: string | null;
  disabled?: boolean;
  onIssueUpdated?: (issue: QualityIssue) => void | Promise<void>;
};

export default function FindingLinkedIssueStatusActions({
  projectId,
  organizationId = null,
  linkedIssueId,
  reportId = null,
  lineId = null,
  disabled = false,
  onIssueUpdated,
}: FindingLinkedIssueStatusActionsProps) {
  const { profile } = useAuth();
  const { isOnline } = useOffline();
  const role = profile?.role;
  const canReadIssues = hasQCPermission(role, "quality_issues:read");
  const [issue, setIssue] = useState<QualityIssue | null>(null);
  const [loading, setLoading] = useState(false);
  const [pendingActionId, setPendingActionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadIssue = useCallback(async () => {
    if (!linkedIssueId || !canReadIssues) {
      setIssue(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const resolved = await resolveLinkedIssueForFindingLine({
        projectId,
        organizationId,
        linkedIssueId,
        isOnline,
      });
      setIssue(resolved);
      if (!resolved) {
        setError("לא ניתן לטעון את פרטי הליקוי המקושר");
      }
    } catch {
      setIssue(null);
      setError("לא ניתן לטעון את פרטי הליקוי המקושר");
    } finally {
      setLoading(false);
    }
  }, [
    linkedIssueId,
    canReadIssues,
    projectId,
    organizationId,
    isOnline,
  ]);

  useEffect(() => {
    void loadIssue();
  }, [loadIssue]);

  if (!canReadIssues || disabled) {
    return null;
  }

  const actions = issue ? getFindingLineIssueStatusActions(issue, role) : [];

  async function handleAction(action: FindingLineIssueAction) {
    if (!issue) {
      return;
    }

    try {
      setPendingActionId(action.id);
      const updated = await updateQualityIssue(
        issue.id,
        buildFindingLineIssueUpdateRequest(action, {
          reportId,
          lineId,
        })
      );
      setIssue(updated);
      if (organizationId) {
        await patchOpenIssuesCacheAfterIssueUpdate({
          organizationId,
          projectId,
          issue: updated,
        });
      }
      showToast(findingLineIssueActionSuccessMessage(action.id), "success");
      await onIssueUpdated?.(updated);
    } catch (updateError) {
      const message =
        updateError instanceof Error
          ? updateError.message
          : "עדכון סטטוס הליקוי נכשל";
      showToast(message, "error");
    } finally {
      setPendingActionId(null);
    }
  }

  if (loading && !issue) {
    return (
      <p className="text-xs text-zinc-500" aria-live="polite">
        טוען סטטוס ליקוי…
      </p>
    );
  }

  if (error && !issue) {
    return (
      <p className="text-xs text-amber-700" role="status">
        {error}
      </p>
    );
  }

  if (!issue) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="warning" className="text-[10px]">
          {QUALITY_ISSUE_STATUS_LABELS_HE[issue.status]}
        </Badge>
        <Badge
          variant={severityBadgeVariant(issue.severity as QualityIssueSeverity)}
          className="text-[10px]"
        >
          {QUALITY_ISSUE_SEVERITY_LABELS_HE[issue.severity]}
        </Badge>
      </div>

      {actions.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {actions.map((action) => (
            <Button
              key={action.id}
              type="button"
              variant="secondary"
              className={`${FR_TOUCH_BUTTON} !px-2 !py-1 text-xs`}
              disabled={pendingActionId !== null}
              onClick={() => void handleAction(action)}
            >
              {pendingActionId === action.id ? "מעדכן..." : action.label}
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
