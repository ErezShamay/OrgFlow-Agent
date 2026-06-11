"use client";

import Link from "next/link";

import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import { useFieldReportSyncContext } from "@/contexts/FieldReportSyncContext";
import { fieldReportDetailPath } from "@/lib/field-reports/routes";
import { FR_TOUCH_BUTTON } from "@/lib/field-reports/touch-input-class";
import { pendingSendPhaseLabelHe } from "@/lib/field-reports/send-queue";
import { fieldReportNetworkStatusLabelHe } from "@/lib/field-reports/sync/network-status";
import {
  buildSyncProgressLabel,
  isSyncPanelUploadEnabled,
  pendingSendReadyBannerText,
  queueEntriesWithErrors,
  shouldShowSyncPanel,
  syncPanelUploadButtonLabel,
  syncPanelUploadDisabledReason,
} from "@/lib/field-reports/sync-panel-view";

export default function SyncPanel() {
  const {
    connectivity,
    canSync,
    checking,
    syncing,
    lastSyncError,
    pendingSendCount,
    queueEntries,
    progress,
    lastRunSummary,
    runSync,
  } = useFieldReportSyncContext();

  const errorEntries = queueEntriesWithErrors(queueEntries);
  const hasQueueErrors = errorEntries.length > 0;
  const visible = shouldShowSyncPanel({
    pendingCount: pendingSendCount,
    syncing,
    hasQueueErrors,
    lastRunSummary,
  });

  if (!visible) {
    return null;
  }

  const uploadEnabled = isSyncPanelUploadEnabled({
    canSync,
    pendingCount: pendingSendCount,
    syncing,
    checking,
  });
  const disabledReason = syncPanelUploadDisabledReason({
    canSync,
    pendingCount: pendingSendCount,
    syncing,
    checking,
  });
  const readyBanner = pendingSendReadyBannerText(pendingSendCount);
  const progressLabel = progress
    ? buildSyncProgressLabel(progress.index, progress.total, progress.phase)
    : null;
  const networkLabel = fieldReportNetworkStatusLabelHe(connectivity);

  return (
    <section
      className="border-b border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-950 dark:border-sky-900 dark:bg-sky-950/40 dark:text-sky-100"
      aria-labelledby="field-report-sync-panel-title"
      role="region"
    >
      <div className="of-container mx-auto flex max-w-3xl flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2
            id="field-report-sync-panel-title"
            className="text-base font-semibold"
          >
            העלאה לשרת
          </h2>
          <p className="text-xs text-sky-800 dark:text-sky-300">
            {checking ? "בודק רשת..." : networkLabel}
          </p>
        </div>

        {readyBanner && !syncing ? (
          <p className="font-medium" role="status">
            {readyBanner}
          </p>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="primary"
            size="lg"
            className={FR_TOUCH_BUTTON}
            disabled={!uploadEnabled}
            onClick={() => void runSync()}
          >
            {syncPanelUploadButtonLabel(syncing)}
          </Button>
          {disabledReason && !syncing ? (
            <p className="text-xs text-sky-800 dark:text-sky-300">
              {disabledReason}
            </p>
          ) : null}
        </div>

        {syncing ? (
          <div
            className="flex flex-wrap items-center gap-2"
            role="status"
            aria-live="polite"
          >
            <Spinner size="sm" label="מסנכרן דוחות" />
            <p>{progressLabel || "מסנכרן דוחות ומסמכים..."}</p>
          </div>
        ) : pendingSendCount > 0 && canSync ? (
          <p className="text-xs text-sky-800 dark:text-sky-300">
            הסנכרון יתחיל אוטומטית כשהשרת זמין - או לחץ «העלה דוחות ומסמכים».
          </p>
        ) : null}

        {lastRunSummary && !syncing ? (
          <p
            className={
              lastRunSummary.failedCount > 0
                ? "text-amber-900 dark:text-amber-200"
                : "text-emerald-800 dark:text-emerald-300"
            }
            role="status"
          >
            {lastRunSummary.messageHe}
          </p>
        ) : null}

        {lastSyncError && !syncing ? (
          <p className="text-sm text-amber-900 dark:text-amber-200">
            {lastSyncError}
          </p>
        ) : null}

        {errorEntries.length > 0 ? (
          <ul className="space-y-2" aria-label="שגיאות סנכרון לפי דוח">
            {errorEntries.map((entry) => (
              <li
                key={entry.clientReportUuid}
                className="rounded-lg border border-amber-200 bg-white/80 px-3 py-2 text-amber-950 dark:border-amber-900 dark:bg-zinc-900/60 dark:text-amber-100"
              >
                <p className="font-medium">{entry.displayLabel}</p>
                {entry.syncPhase ? (
                  <p className="text-xs text-amber-800 dark:text-amber-300">
                    {pendingSendPhaseLabelHe(entry.syncPhase)}
                  </p>
                ) : null}
                {entry.lastError ? (
                  <p className="mt-1 text-sm">{entry.lastError}</p>
                ) : null}
                <Link
                  href={fieldReportDetailPath(entry.reportId)}
                  className="mt-1 inline-block text-xs font-medium text-brand hover:underline"
                >
                  פתח דוח
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  );
}
