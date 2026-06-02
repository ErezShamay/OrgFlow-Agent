"use client";

import Link from "next/link";

import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import { FR_TOUCH_BUTTON } from "@/lib/field-reports/touch-input-class";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { useFieldReportOfflinePrep } from "@/hooks/useFieldReportOfflinePrep";
import { useCallback, useEffect, useState } from "react";

type VisitReport = {
  id: string;
  project_name?: string;
  visit_type_label_he: string;
  status_label_he: string;
  visit_date: string;
  status: string;
};

const STATUS_FILTERS = [
  { value: "", label: "הכל" },
  { value: "IN_PROGRESS", label: "בעבודה" },
  { value: "CLOSED", label: "סגור" },
  { value: "PENDING_UPLOAD", label: "ממתין לשליחה" },
  { value: "LOCKED", label: "נעול" },
] as const;

export default function FieldReportsPage() {
  const { status, isEnabled, loading, error, reload } =
    useFieldReportModule();
  const offlinePrep = useFieldReportOfflinePrep();
  const [reports, setReports] = useState<VisitReport[]>([]);
  const [inProgressCount, setInProgressCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportsError, setReportsError] = useState("");

  const loadInProgressCount = useCallback(async function loadInProgressCount() {
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
  }, []);

  const loadReports = useCallback(async function loadReports(
    status: string = statusFilter
  ) {
    try {
      setReportsLoading(true);
      setReportsError("");

      const query = status
        ? `?status=${encodeURIComponent(status)}`
        : "";
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
      const nextReports = payload.reports || [];
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
    }
  }, [statusFilter]);

  useEffect(() => {
    if (!isEnabled) {
      return;
    }

    const timer = window.setTimeout(() => {
      void loadReports(statusFilter);
      if (statusFilter !== "IN_PROGRESS") {
        void loadInProgressCount();
      }
    }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [isEnabled, statusFilter, loadReports, loadInProgressCount]);

  if (loading) {
    return (
      <div className="of-container mx-auto max-w-3xl p-8 text-sm text-zinc-500">
        טוען מודול הפקת דוחות...
      </div>
    );
  }

  if (error) {
    return (
      <div className="of-container mx-auto max-w-3xl space-y-4 p-8">
        <p className="text-sm text-red-600">{error}</p>
        <Button variant="secondary" onClick={() => void reload()}>
          נסה שוב
        </Button>
      </div>
    );
  }

  if (!isEnabled) {
    return (
      <div className="of-container mx-auto max-w-3xl space-y-4 p-8">
        <h1 className="of-page-title text-2xl">הפקת דוחות</h1>
        <p className="of-page-desc text-sm">
          מודול הפקת דוחות אינו מופעל עבור הארגון הנוכחי. פנה למנהל המערכת
          (ספק) להפעלה.
        </p>
        {status?.storage_available === false ? (
          <p className="text-sm text-amber-700 dark:text-amber-400">
            המיגרציה למסד הנתונים טרם הורצה — נדרשת הגדרת תשתית.
          </p>
        ) : null}
        <Link href="/" className="text-sm text-brand hover:underline">
          חזרה לדף הבית
        </Link>
      </div>
    );
  }

  return (
    <div className="of-container mx-auto max-w-3xl space-y-6 p-4 md:p-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="of-page-title text-2xl">הפקת דוחות</h1>
          <p className="of-page-desc text-sm">הדוחות שלי</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge>מודול פעיל</Badge>
          <Button
            variant="secondary"
            size="lg"
            className={FR_TOUCH_BUTTON}
            disabled={offlinePrep.loading}
            onClick={() => void offlinePrep.prepare()}
          >
            {offlinePrep.loading
              ? "מכין..."
              : "הכנה לא מקוון"}
          </Button>
          <Link
            href="/field-reports/new"
            className="of-focus-ring inline-flex min-h-12 touch-manipulation items-center justify-center rounded-2xl bg-brand px-5 py-2.5 text-base font-semibold text-white transition-all hover:bg-brand-dark dark:bg-brand-light dark:text-brand-dark lg:min-h-0 lg:px-4 lg:py-2 lg:text-sm"
          >
            דוח ביקור חדש
          </Link>
        </div>
      </header>

      {offlinePrep.isReady ? (
        <p className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
          מוכן לעבודה ללא רשת עד{" "}
          {offlinePrep.expiresAt
            ? new Date(offlinePrep.expiresAt).toLocaleString("he-IL")
            : "—"}
          {offlinePrep.catalogVersion
            ? ` · קטלוג ${offlinePrep.catalogVersion}`
            : ""}
        </p>
      ) : null}

      {offlinePrep.error ? (
        <p className="text-sm text-red-600">{offlinePrep.error}</p>
      ) : null}

      {inProgressCount > 0 && statusFilter !== "IN_PROGRESS" ? (
        <p className="text-sm text-zinc-600">
          {inProgressCount} דוחות בעבודה — ניתן לערוך דוח אחד בכל רגע במכשיר.
          <button
            type="button"
            className="mr-2 text-brand hover:underline"
            onClick={() => setStatusFilter("IN_PROGRESS")}
          >
            הצג רק בעבודה
          </button>
        </p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map((filter) => {
          const isActive = statusFilter === filter.value;
          return (
            <button
              key={filter.value || "all"}
              type="button"
              className={
                isActive
                  ? "min-h-11 touch-manipulation rounded-full bg-brand px-4 py-2 text-sm font-medium text-white lg:min-h-0 lg:px-3 lg:py-1.5"
                  : "min-h-11 touch-manipulation rounded-full border border-zinc-300 px-4 py-2 text-sm text-zinc-700 hover:border-brand dark:border-zinc-700 dark:text-zinc-200 lg:min-h-0 lg:px-3 lg:py-1.5"
              }
              onClick={() => setStatusFilter(filter.value)}
            >
              {filter.label}
            </button>
          );
        })}
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
          <Button
            variant="secondary"
            onClick={() => void loadReports(statusFilter)}
          >
            נסה שוב
          </Button>
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
          <p className="text-sm text-zinc-600">אין דוחות עדיין.</p>
          <Link
            href="/field-reports/new"
            className="of-focus-ring mt-4 inline-flex items-center justify-center rounded-2xl bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark"
          >
            צור דוח ביקור ראשון
          </Link>
        </div>
      ) : (
        <ul className="divide-y divide-zinc-200 rounded-xl border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
          {reports.map((report) => (
            <li key={report.id}>
              <Link
                href={`/field-reports/${report.id}`}
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
                <Badge>{report.status_label_he}</Badge>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
