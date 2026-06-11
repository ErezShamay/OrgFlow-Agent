"use client";

import Badge from "@/components/ui/Badge";
import IssueEventsTimeline from "@/components/quality-issues/IssueEventsTimeline";
import IssueStatusActions from "@/components/quality-issues/IssueStatusActions";
import {
  formatIssueDate,
  severityBadgeVariant,
  statusBadgeVariant,
} from "@/components/quality-issues/IssuesTable";
import { buildIssueDetailFields } from "@/lib/quality-issues/issue-detail";
import {
  QUALITY_ISSUE_SEVERITY_LABELS_HE,
  QUALITY_ISSUE_STATUS_LABELS_HE,
  type QualityIssue,
  type QualityIssueCatalogLink,
  type QualityIssueEvent,
} from "@/lib/quality-issues/types";

export type IssueDetailPanelProps = {
  issue: QualityIssue;
  events: QualityIssueEvent[];
  catalogLink?: QualityIssueCatalogLink | null;
  actorRole?: string | null;
  onIssueUpdated?: () => void | Promise<void>;
  className?: string;
};

export default function IssueDetailPanel({
  issue,
  events,
  catalogLink = null,
  actorRole = null,
  onIssueUpdated,
  className = "",
}: IssueDetailPanelProps) {
  const detailFields = buildIssueDetailFields(issue, catalogLink);

  return (
    <div className={`space-y-6 ${className}`}>
      <section className="of-card of-card-p8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-3">
            <h2 className="text-2xl font-bold">{issue.title}</h2>
            <div className="flex flex-wrap gap-2">
              <Badge variant={statusBadgeVariant(issue.status)}>
                {QUALITY_ISSUE_STATUS_LABELS_HE[issue.status]}
              </Badge>
              <Badge variant={severityBadgeVariant(issue.severity)}>
                {QUALITY_ISSUE_SEVERITY_LABELS_HE[issue.severity]}
              </Badge>
            </div>
          </div>
          <IssueStatusActions
            issue={issue}
            role={actorRole}
            onUpdated={onIssueUpdated}
          />
        </div>

        {issue.description?.trim() ? (
          <p className="mt-6 leading-relaxed text-zinc-700 dark:text-zinc-300">
            {issue.description}
          </p>
        ) : null}

        {detailFields.length > 0 ? (
          <dl className="mt-8 grid gap-4 sm:grid-cols-2">
            {detailFields.map((field) => (
              <div key={field.label}>
                <dt className="text-sm font-medium text-zinc-500">
                  {field.label}
                </dt>
                <dd className="mt-1 text-sm text-zinc-800 dark:text-zinc-200">
                  {field.value}
                </dd>
              </div>
            ))}
          </dl>
        ) : null}

        <p className="mt-8 text-xs text-zinc-500">
          עודכן לאחרונה: {formatIssueDate(issue.updated_at ?? issue.last_seen_at)}
        </p>
      </section>

      <IssueEventsTimeline events={events} />
    </div>
  );
}
