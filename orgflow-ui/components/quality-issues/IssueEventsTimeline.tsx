"use client";

import {
  formatIssueDateTime,
  formatQualityIssueEventDetails,
  formatQualityIssueEventSummary,
  sortQualityIssueEvents,
} from "@/lib/quality-issues/issue-detail";
import type { QualityIssueEvent } from "@/lib/quality-issues/types";

export type IssueEventsTimelineProps = {
  events: QualityIssueEvent[];
  className?: string;
};

export default function IssueEventsTimeline({
  events,
  className = "",
}: IssueEventsTimelineProps) {
  const sortedEvents = sortQualityIssueEvents(events);

  return (
    <section
      className={`of-card of-card-p8 ${className}`}
      aria-label="היסטוריית ליקוי"
    >
      <div className="mb-6">
        <h2 className="text-xl font-bold">היסטוריה</h2>
        <p className="mt-1 text-sm text-zinc-500">
          אירועי מעקב מה-registry
        </p>
      </div>

      {sortedEvents.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-zinc-300 px-4 py-10 text-center text-sm text-zinc-500 dark:border-zinc-700">
          אין אירועים רשומים עדיין
        </div>
      ) : (
        <ol className="space-y-4">
          {sortedEvents.map((event) => {
            const details = formatQualityIssueEventDetails(event);

            return (
              <li
                key={event.id}
                className="rounded-2xl border border-zinc-200 px-4 py-4 dark:border-zinc-800"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <p className="font-semibold">
                    {formatQualityIssueEventSummary(event)}
                  </p>
                  <time
                    className="text-sm text-zinc-500"
                    dateTime={event.created_at ?? undefined}
                  >
                    {formatIssueDateTime(event.created_at)}
                  </time>
                </div>

                {details.length > 0 ? (
                  <ul className="mt-2 space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
                    {details.map((detail) => (
                      <li key={detail}>{detail}</li>
                    ))}
                  </ul>
                ) : null}

                {event.report_id ? (
                  <p className="mt-2 text-xs text-zinc-500">
                    דוח: {event.report_id}
                  </p>
                ) : null}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
