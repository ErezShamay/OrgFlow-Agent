"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import FieldReportsOfflineGuide from "@/components/field-reports/FieldReportsOfflineGuide";
import ProjectPickerDialog from "@/components/field-reports/ProjectPickerDialog";
import Badge from "@/components/ui/Badge";
import LoadingState from "@/components/ui/LoadingState";
import { apiFetch } from "@/lib/api/client";
import { FIELD_REPORTS_UPLOAD_ROUTE } from "@/lib/qc-navigation";
import { fieldReportDetailPath, projectFieldReportNewPath } from "@/lib/field-reports/routes";
import { isFieldReportVisibleInList } from "@/lib/field-reports/field-report-list";
import {
  fieldReportListStatusLabel,
  isFieldReportPendingPublish,
} from "@/lib/field-reports/publish-list";
import {
  FR_FILTER_BUTTON_ACTIVE,
  FR_FILTER_BUTTON_INACTIVE,
  FR_PRIMARY_ACTION_BUTTON,
} from "@/lib/field-reports/touch-input-class";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { useFieldReportOfflinePrep } from "@/hooks/useFieldReportOfflinePrep";
import {
  clearOfflinePrepUiDismiss,
  isOfflinePrepUiDismissed,
  saveOfflinePrepUiDismiss,
} from "@/lib/field-reports/offline-prep-ui-dismiss";
import { useCallback, useEffect, useState } from "react";

type VisitReport = {
  id: string;
  project_name?: string;
  visit_type_label_he: string;
  status_label_he: string;
  visit_date: string;
  status: string;
  pending_publish?: boolean;
  is_published?: boolean;
  can_publish?: boolean;
};

const STATUS_FILTERS = [
  { value: "", label: "הכל" },
  { value: "IN_PROGRESS", label: "בעבודה" },
  { value: "CLOSED", label: "סגור" },
  { value: "PENDING_PUBLISH", label: "ממתין לפרסום" },
  { value: "PENDING_UPLOAD", label: "ממתין לשליחה" },
] as const;

export default function FieldReportsPage() {
  const searchParams = useSearchParams();
  const projectFilter = searchParams.get("project")?.trim() ?? "";
  const { status, isEnabled, loading, error, reload } =
    useFieldReportModule();
  const offlinePrep = useFieldReportOfflinePrep({ autoPrepare: false });
  const organizationId = status?.organization_id || "";
  const [reports, setReports] = useState<VisitReport[]>([]);
  const [inProgressCount, setInProgressCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [reportsLoading, setReportsLoading] = useState(false);
  const [initialReportsReady, setInitialReportsReady] = useState(false);
  const [reportsError, setReportsError] = useState("");
  const [showOfflineGuide, setShowOfflineGuide] = useState(true);
  const [projectPickerOpen, setProjectPickerOpen] = useState(false);
  const importedInProgressCount = offlinePrep.importSummary
    ? offlinePrep.importSummary.imported + offlinePrep.importSummary.updated
    : 0;

  const offlinePrepFingerprint = {
    expiresAt: offlinePrep.expiresAt,
    catalogVersion: offlinePrep.catalogVersion,
  };

  useEffect(() => {
    if (!organizationId || !offlinePrep.isReady) {
      setShowOfflineGuide(true);
      return;
    }

    setShowOfflineGuide(
      !isOfflinePrepUiDismissed(
        organizationId,
        "guide",
        offlinePrepFingerprint
      )
    );
  }, [
    organizationId,
    offlinePrep.isReady,
    offlinePrep.expiresAt,
    offlinePrep.catalogVersion,
  ]);

  function dismissOfflineGuide() {
    if (!organizationId) {
      return;
    }

    saveOfflinePrepUiDismiss(
      organizationId,
      "guide",
      offlinePrepFingerprint
    );
    setShowOfflineGuide(false);
  }

  async function handleCancelOfflinePrep() {
    await offlinePrep.cancel();
    setShowOfflineGuide(true);
  }

  async function handleOfflinePrep() {
    const saved = await offlinePrep.prepare();
    if (saved) {
      if (organizationId) {
        clearOfflinePrepUiDismiss(organizationId);
      }
      setShowOfflineGuide(true);
    }
  }

  const loadInProgressCount = useCallback(async function loadInProgressCount() {
    if (projectFilter) {
      return;
    }

    try {
      const response = await apiFetch(
        "/field-reports/visits?status=IN_PROGRESS"
      );
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      setInProgressCount((payload.reports || []).length);
    } catch {
      setInProgressCount(0);
    }
  }, [projectFilter]);

  const loadReports = useCallback(async function loadReports(
    status: string = statusFilter
  ) {
    try {
      setReportsLoading(true);
      setReportsError("");

      const params = new URLSearchParams();
      if (projectFilter) {
        params.set("project_id", projectFilter);
      }
      if (status && status !== "PENDING_PUBLISH") {
        params.set("status", status);
      } else if (status === "PENDING_PUBLISH") {
        params.set("status", "CLOSED");
      }
      const query = params.toString() ? `?${params.toString()}` : "";
      const response = await apiFetch(`/field-reports/visits${query}`);

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(
          payload.error?.message
            || payload.message
            || "טעינת רשימת הדוחות נכשלה"
        );
      }

      const payload = await response.json();
      let nextReports = (payload.reports || []).filter(
        (report: VisitReport) =>
          isFieldReportVisibleInList(report.status)
      );
      if (status === "PENDING_PUBLISH") {
        nextReports = nextReports.filter((report: VisitReport) =>
          isFieldReportPendingPublish(report)
        );
      }
      setReports(nextReports);
      if (status === "IN_PROGRESS") {
        setInProgressCount(nextReports.length);
      }
    } catch (err: unknown) {
      setReportsError(
        err instanceof Error
          ? err.message
          : "טעינת רשימת הדוחות נכשלה"
      );
    } finally {
      setReportsLoading(false);
      setInitialReportsReady(true);
    }
  }, [statusFilter, projectFilter]);

  useEffect(() => {
    setInitialReportsReady(false);
    setReports([]);
    setInProgressCount(0);
    setReportsError("");
  }, [organizationId, projectFilter]);

  useEffect(() => {
    if (!isEnabled) {
      return;
    }

    void loadReports(statusFilter);
    if (statusFilter !== "IN_PROGRESS") {
      void loadInProgressCount();
    }
  }, [isEnabled, statusFilter, loadReports, loadInProgressCount]);

  useEffect(() => {
    if (!isEnabled) {
      return;
    }

    const handleSyncComplete = () => {
      void loadReports(statusFilter);
      if (statusFilter !== "IN_PROGRESS") {
        void loadInProgressCount();
      }
    };

    window.addEventListener(
      "field-report-sync-complete",
      handleSyncComplete
    );

    return () => {
      window.removeEventListener(
        "field-report-sync-complete",
        handleSyncComplete
      );
    };
  }, [isEnabled, statusFilter, loadReports, loadInProgressCount]);

  const bootstrapping =
    (loading && !status && !error)
    || (isEnabled && !initialReportsReady && !reportsError);

  if (bootstrapping) {
    return (
      <div className="of-container mx-auto max-w-3xl p-8">
        <LoadingState message="טוען הפקת דוחות..." variant="spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="of-container mx-auto max-w-3xl space-y-4 p-8">
        <p className="text-sm text-red-600">{error}</p>
        <button
          type="button"
          className={FR_PRIMARY_ACTION_BUTTON}
          onClick={() => void reload()}
        >
          נסה שוב
        </button>
      </div>
    );
  }

  if (!isEnabled) {
    return (
      <div className="of-container mx-auto max-w-3xl space-y-4 p-8">
        <h1 className="of-page-title text-2xl">הפקת דוחות</h1>
        <p className="of-page-desc text-sm">
          מודול הפקת דוחות אינו מופעל עבור הארגון הנוכחי. פנה למנהל המערכת
          להפעלה.
        </p>
        {status?.storage_available === false ? (
          <p className="text-sm text-amber-700 dark:text-amber-400">
            המיגרציה למסד הנתונים טרם הורצה - נדרשת הגדרת תשתית.
          </p>
        ) : null}
        <Link href="/" className="text-sm text-brand hover:underline">
          חזרה לדף הבית
        </Link>
      </div>
    );
  }

  const statusFilterButtons = (
    <div className="flex flex-wrap gap-2">
      {STATUS_FILTERS.map((filter) => {
        const isActive = statusFilter === filter.value;
        return (
          <button
            key={filter.value || "all"}
            type="button"
            className={
              isActive
                ? FR_FILTER_BUTTON_ACTIVE
                : FR_FILTER_BUTTON_INACTIVE
            }
            onClick={() => setStatusFilter(filter.value)}
          >
            {filter.label}
          </button>
        );
      })}
    </div>
  );

  const inProgressHint =
    !projectFilter
    && inProgressCount > 0
    && statusFilter !== "IN_PROGRESS" ? (
      <p className="text-sm text-zinc-600 dark:text-zinc-300">
        {inProgressCount} דוחות בעבודה - ניתן לערוך דוח אחד בכל רגע במכשיר.
        <button
          type="button"
          className="mr-2 text-brand hover:underline"
          onClick={() => setStatusFilter("IN_PROGRESS")}
        >
          הצג רק בעבודה
        </button>
      </p>
    ) : null;

  const pageTitle = projectFilter ? "דוחות שטח לפרויקט" : "הפקת דוחות";
  const pageSubtitle = projectFilter ? "כל הדוחות לפרויקט" : "הדוחות שלי";

  return (
    <div className="of-container mx-auto max-w-3xl space-y-6 p-4 md:p-8">
      {projectFilter ? (
        <Link
          href={`/projects/${encodeURIComponent(projectFilter)}`}
          className="text-sm text-brand hover:underline"
        >
          ← חזרה לפרויקט
        </Link>
      ) : null}
      <header className="hidden flex-wrap items-center justify-between gap-4 lg:flex">
        <div className="space-y-1">
          <h1 className="of-page-title text-2xl">{pageTitle}</h1>
          <p className="of-page-desc text-sm">{pageSubtitle}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {projectFilter ? (
            <Link
              href={projectFieldReportNewPath(projectFilter)}
              className={FR_PRIMARY_ACTION_BUTTON}
            >
              הפקת דוח
            </Link>
          ) : (
            <button
              type="button"
              className={FR_PRIMARY_ACTION_BUTTON}
              onClick={() => setProjectPickerOpen(true)}
            >
              הפקת דוח
            </button>
          )}
          <Link
            href={FIELD_REPORTS_UPLOAD_ROUTE.href}
            className={FR_PRIMARY_ACTION_BUTTON}
          >
            {FIELD_REPORTS_UPLOAD_ROUTE.label}
          </Link>
          <button
            type="button"
            className={FR_PRIMARY_ACTION_BUTTON}
            disabled={offlinePrep.loading}
            onClick={() => void handleOfflinePrep()}
          >
            {offlinePrep.loading
              ? "מכין..."
              : "הכנה לא מקוון"}
          </button>
        </div>
      </header>

      <header className="space-y-1 lg:hidden">
        <h1 className="of-page-title text-2xl">{pageTitle}</h1>
        <p className="of-page-desc text-sm">{pageSubtitle}</p>
      </header>

      <section
        className="
          space-y-3
          rounded-2xl
          border
          border-zinc-200
          bg-white
          p-4
          dark:border-zinc-800
          dark:bg-zinc-900
          md:p-5
          lg:hidden
        "
      >
        <h2 className="text-sm font-semibold text-zinc-500 dark:text-zinc-400">
          פעולות
        </h2>
        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          {projectFilter ? (
            <Link
              href={projectFieldReportNewPath(projectFilter)}
              className={`${FR_PRIMARY_ACTION_BUTTON} w-full sm:w-auto`}
            >
              הפקת דוח
            </Link>
          ) : (
            <button
              type="button"
              className={`${FR_PRIMARY_ACTION_BUTTON} w-full sm:w-auto`}
              onClick={() => setProjectPickerOpen(true)}
            >
              הפקת דוח
            </button>
          )}
          <Link
            href={FIELD_REPORTS_UPLOAD_ROUTE.href}
            className={`${FR_FILTER_BUTTON_INACTIVE} w-full sm:w-auto`}
          >
            {FIELD_REPORTS_UPLOAD_ROUTE.label}
          </Link>
          <button
            type="button"
            className={`${FR_FILTER_BUTTON_INACTIVE} w-full sm:w-auto`}
            disabled={offlinePrep.loading}
            onClick={() => void handleOfflinePrep()}
          >
            {offlinePrep.loading
              ? "מכין..."
              : "הכנה לא מקוון"}
          </button>
        </div>
      </section>

      <ProjectPickerDialog
        open={projectPickerOpen}
        onClose={() => setProjectPickerOpen(false)}
      />

      {offlinePrep.isReady ? (
        <div
          role="status"
          className="flex flex-wrap items-start justify-between gap-3 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"
        >
          <p>
            מוכן לעבודה ללא רשת עד{" "}
            {offlinePrep.expiresAt
              ? new Date(offlinePrep.expiresAt).toLocaleString("he-IL")
              : "-"}
            {offlinePrep.catalogVersion
              ? ` · קטלוג ${offlinePrep.catalogVersion}`
              : ""}
          </p>
          <button
            type="button"
            className="shrink-0 text-xs font-medium text-emerald-800 underline-offset-2 hover:underline disabled:opacity-50 dark:text-emerald-300"
            disabled={offlinePrep.cancelling}
            onClick={() => void handleCancelOfflinePrep()}
          >
            {offlinePrep.cancelling ? "מבטל..." : "בטל הכנה לא מקוון"}
          </button>
        </div>
      ) : null}

      {offlinePrep.isReady && showOfflineGuide ? (
        <FieldReportsOfflineGuide
          expiresAt={offlinePrep.expiresAt}
          catalogVersion={offlinePrep.catalogVersion}
          importedInProgressCount={importedInProgressCount}
          dismissible
          onDismiss={dismissOfflineGuide}
        />
      ) : null}

      {offlinePrep.error ? (
        <p className="text-sm text-red-600">{offlinePrep.error}</p>
      ) : null}

      <section
        className="
          space-y-3
          rounded-2xl
          border
          border-zinc-200
          bg-white
          p-4
          dark:border-zinc-800
          dark:bg-zinc-900
          md:p-5
          lg:hidden
        "
      >
        <h2 className="text-sm font-semibold text-zinc-500 dark:text-zinc-400">
          סינון
        </h2>
        {inProgressHint}
        {statusFilterButtons}
      </section>

      <div className="hidden space-y-4 lg:block">
        {inProgressHint}
        {statusFilterButtons}
      </div>

      {reportsLoading ? (
        <p className="text-sm text-zinc-500">טוען דוחות...</p>
      ) : reportsError ? (
        <div className="space-y-2">
          <p className="text-sm text-red-600">{reportsError}</p>
          {reportsError.includes("מיגרציה") ? (
            <p className="text-xs text-zinc-500">
              הרץ ב-Supabase:{" "}
              <code className="rounded bg-zinc-100 px-1 dark:bg-zinc-800">
                db/migrations/2026060102_field_visit_reports.sql
              </code>
            </p>
          ) : null}
          <button
            type="button"
            className={FR_PRIMARY_ACTION_BUTTON}
            onClick={() => void loadReports(statusFilter)}
          >
            נסה שוב
          </button>
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
          <p className="text-sm text-zinc-600">
            {projectFilter ? "אין דוחות לפרויקט זה עדיין." : "אין דוחות עדיין."}
          </p>
          <p className="mt-2 text-sm text-zinc-500">
            {projectFilter
              ? "ליצירת דוח חדש לחץ על «הפקת דוח»."
              : "ליצירת דוח חדש לחץ על «הפקת דוח» ובחר פרויקט."}
          </p>
          {projectFilter ? (
            <Link
              href={projectFieldReportNewPath(projectFilter)}
              className={`${FR_PRIMARY_ACTION_BUTTON} mt-4 inline-flex`}
            >
              הפקת דוח
            </Link>
          ) : (
            <button
              type="button"
              className={`${FR_PRIMARY_ACTION_BUTTON} mt-4`}
              onClick={() => setProjectPickerOpen(true)}
            >
              הפקת דוח
            </button>
          )}
        </div>
      ) : (
        <ul className="divide-y divide-zinc-200 rounded-xl border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
          {reports.map((report) => (
            <li key={report.id}>
              <Link
                href={fieldReportDetailPath(report.id)}
                className="flex min-h-14 touch-manipulation flex-wrap items-center justify-between gap-3 px-4 py-4 hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
              >
                <div>
                  <p className="font-medium">
                    {report.project_name || "פרויקט"}
                  </p>
                  <p className="text-sm text-zinc-500">
                    {report.visit_type_label_he} · {report.visit_date}
                  </p>
                </div>
                <Badge>{fieldReportListStatusLabel(report)}</Badge>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
