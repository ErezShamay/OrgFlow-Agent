"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { severityBadgeVariant } from "@/components/quality-issues/IssuesTable";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { useDebouncedCallback } from "@/hooks/useDebouncedCallback";
import { useOffline } from "@/providers/OfflineProvider";
import {
  FINDING_MATCH_DEBOUNCE_MS,
  buildSuggestMatchesRequestFromFindingRow,
  formatSimilarIssueSummary,
  hasMatchableFindingFields,
  type FindingRowMatchFields,
} from "@/lib/quality-issues/finding-match-hints";
import { hasQCPermission } from "@/lib/quality-issues/permissions";
import { resolveProjectQualityIssueMatches } from "@/lib/quality-issues/suggest-matches-resolver";
import {
  QUALITY_ISSUE_SEVERITY_LABELS_HE,
  QUALITY_ISSUE_STATUS_LABELS_HE,
  type QualityIssueMatchCandidate,
  type QualityIssueSeverity,
} from "@/lib/quality-issues/types";
import FindingLinkedIssueStatusActions from "@/components/quality-issues/FindingLinkedIssueStatusActions";
import { FR_TOUCH_BUTTON } from "@/lib/field-reports/touch-input-class";

const MAX_VISIBLE_MATCHES = 3;

type FindingSimilarIssuesHintProps = FindingRowMatchFields & {
  projectId?: string | null;
  organizationId?: string | null;
  reportId?: string | null;
  lineId?: string | null;
  disabled?: boolean;
  linkedIssueId?: string | null;
  linking?: boolean;
  onLinkIssue?: (issueId: string) => void | Promise<void>;
  onMarkNewIssue?: () => void | Promise<void>;
  onUnlinkIssue?: () => void | Promise<void>;
};

export default function FindingSimilarIssuesHint({
  projectId,
  organizationId = null,
  reportId = null,
  lineId = null,
  disabled = false,
  linkedIssueId = null,
  linking = false,
  onLinkIssue,
  onMarkNewIssue,
  onUnlinkIssue,
  ...fields
}: FindingSimilarIssuesHintProps) {
  const { profile } = useAuth();
  const { isOnline } = useOffline();
  const canReadIssues = hasQCPermission(
    profile?.role,
    "quality_issues:read"
  );
  const canLinkIssues =
    canReadIssues &&
    hasQCPermission(profile?.role, "field_reports:write") &&
    Boolean(onLinkIssue || onMarkNewIssue || onUnlinkIssue);
  const [matches, setMatches] = useState<QualityIssueMatchCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userChoseNew, setUserChoseNew] = useState(false);

  const debouncedFetch = useDebouncedCallback(async () => {
    if (!projectId || !canReadIssues || disabled || linkedIssueId) {
      setMatches([]);
      setLoading(false);
      setError(null);
      return;
    }

    if (!hasMatchableFindingFields(fields)) {
      setMatches([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await resolveProjectQualityIssueMatches({
        projectId,
        organizationId,
        request: buildSuggestMatchesRequestFromFindingRow(fields),
        isOnline,
      });
      setMatches(response.candidates);
    } catch {
      setMatches([]);
      setError("לא ניתן לטעון ליקויים דומים");
    } finally {
      setLoading(false);
    }
  }, FINDING_MATCH_DEBOUNCE_MS);

  useEffect(() => {
    setUserChoseNew(false);
  }, [fields.location, fields.trade, fields.group_key, fields.issue_id]);

  useEffect(() => {
    debouncedFetch();
  }, [
    projectId,
    organizationId,
    isOnline,
    canReadIssues,
    disabled,
    linkedIssueId,
    fields.location,
    fields.trade,
    fields.group_key,
    fields.issue_id,
    debouncedFetch,
  ]);

  if (!projectId || !canReadIssues || disabled) {
    return null;
  }

  if (linkedIssueId) {
    const linkedMatch = matches.find(
      (candidate) => candidate.issue.id === linkedIssueId
    );
    const linkedTitle =
      linkedMatch?.issue.title ||
      formatSimilarIssueSummary({
        title: "ליקוי מקושר",
        location: fields.location,
        trade: fields.trade,
      });

    return (
      <div
        className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-950"
        role="status"
      >
        <p className="font-medium">מקושר לליקוי קיים: {linkedTitle}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          <Link
            href={`/projects/${encodeURIComponent(projectId)}/issues/${encodeURIComponent(linkedIssueId)}`}
            className="font-medium text-brand underline-offset-2 hover:underline"
          >
            צפייה בליקוי
          </Link>
          {canLinkIssues && onUnlinkIssue ? (
            <Button
              type="button"
              variant="secondary"
              className={`${FR_TOUCH_BUTTON} !px-2 !py-1 text-xs`}
              disabled={linking}
              onClick={() => void onUnlinkIssue()}
            >
              {linking ? "מבטל..." : "בטל קישור"}
            </Button>
          ) : null}
        </div>
        <div className="mt-3 border-t border-emerald-200/80 pt-3">
          <FindingLinkedIssueStatusActions
            projectId={projectId}
            organizationId={organizationId}
            linkedIssueId={linkedIssueId}
            reportId={reportId}
            lineId={lineId}
            disabled={disabled}
          />
        </div>
      </div>
    );
  }

  if (userChoseNew) {
    return (
      <p
        className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-700"
        role="status"
      >
        ייווצר ליקוי חדש בסגירת הדוח.
      </p>
    );
  }

  if (!hasMatchableFindingFields(fields)) {
    return null;
  }

  if (loading && matches.length === 0) {
    return (
      <p className="text-xs text-zinc-500" aria-live="polite">
        בודק ליקויים דומים…
      </p>
    );
  }

  if (error) {
    return (
      <p className="text-xs text-amber-700" role="status">
        {error}
      </p>
    );
  }

  if (matches.length === 0) {
    return null;
  }

  const visibleMatches = matches.slice(0, MAX_VISIBLE_MATCHES);
  const hiddenCount = matches.length - visibleMatches.length;

  return (
    <div
      className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950"
      role="status"
      aria-live="polite"
    >
      <p className="font-medium">ליקוי דומה קיים</p>
      <ul className="mt-1 space-y-2">
        {visibleMatches.map((candidate) => {
          const issue = candidate.issue;
          const summary = formatSimilarIssueSummary({
            title: issue.title,
            location: issue.location,
            trade: issue.trade,
          });

          return (
            <li
              key={issue.id}
              className="flex flex-wrap items-center gap-x-2 gap-y-1"
            >
              <span>{summary}</span>
              <Badge variant="warning" className="text-[10px]">
                {QUALITY_ISSUE_STATUS_LABELS_HE[issue.status]}
              </Badge>
              <Badge
                variant={severityBadgeVariant(
                  issue.severity as QualityIssueSeverity
                )}
                className="text-[10px]"
              >
                {QUALITY_ISSUE_SEVERITY_LABELS_HE[issue.severity]}
              </Badge>
              <Link
                href={`/projects/${encodeURIComponent(projectId)}/issues/${encodeURIComponent(issue.id)}`}
                className="font-medium text-brand underline-offset-2 hover:underline"
              >
                צפייה
              </Link>
              {canLinkIssues && onLinkIssue ? (
                <Button
                  type="button"
                  variant="secondary"
                  className={`${FR_TOUCH_BUTTON} !px-2 !py-1 text-xs`}
                  disabled={linking}
                  onClick={() => void onLinkIssue(issue.id)}
                >
                  {linking ? "מקשר..." : "קשר לליקוי"}
                </Button>
              ) : null}
            </li>
          );
        })}
      </ul>
      {hiddenCount > 0 ? (
        <p className="mt-1 text-amber-800">ועוד {hiddenCount} ליקויים דומים</p>
      ) : null}
      {canLinkIssues && onMarkNewIssue ? (
        <div className="mt-2 border-t border-amber-200/80 pt-2">
          <Button
            type="button"
            variant="secondary"
            className={`${FR_TOUCH_BUTTON} !px-2 !py-1 text-xs`}
            disabled={linking}
            onClick={() => {
              setUserChoseNew(true);
              void onMarkNewIssue();
            }}
          >
            ליקוי חדש (ללא קישור)
          </Button>
        </div>
      ) : null}
    </div>
  );
}
