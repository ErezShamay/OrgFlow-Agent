"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import Button from "@/components/ui/Button";
import LoadingState from "@/components/ui/LoadingState";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { apiFetch } from "@/lib/api/client";

type ArchivedFieldReport = {
  id: string;
  visit_date: string;
  visit_type_label_he: string;
  pdf_filename: string;
  locked_at?: string | null;
};

type ArchiveMonth = {
  month: number;
  month_label_he: string;
  reports: ArchivedFieldReport[];
};

type ArchiveYear = {
  year: number;
  months: ArchiveMonth[];
};

type FieldReportArchive = {
  project_id: string;
  years: ArchiveYear[];
  total_reports: number;
};

type UploadedReport = {
  id: string;
  title: string;
  report_source: string;
  created_at?: string | null;
  text_preview?: string | null;
  recommended_action?: string | null;
  original_filename?: string | null;
};

type UploadedReportsArchive = {
  project_id: string;
  reports: UploadedReport[];
  total_reports: number;
};

type DocumentFilter = "all" | "field" | "upload";

type Props = {
  projectId: string;
};

const REPORT_SOURCE_LABELS: Record<string, string> = {
  DELAY: "עיכוב",
  QUALITY: "איכות",
  SAFETY: "בטיחות",
  PROGRESS: "התקדמות",
  GENERAL: "כללי",
  UNKNOWN: "לא מסווג",
};

const FILTER_OPTIONS: Array<{ id: DocumentFilter; label: string }> = [
  { id: "all", label: "הכל" },
  { id: "field", label: "דוחות שטח" },
  { id: "upload", label: "העלאות AI" },
];

function formatDateTime(value?: string | null) {
  if (!value) {
    return "תאריך לא זמין";
  }

  try {
    return new Date(value).toLocaleString("he-IL");
  } catch {
    return value;
  }
}

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleDateString("he-IL");
  } catch {
    return value;
  }
}

function getReportSourceLabel(source: string) {
  const normalized = source.trim().toUpperCase();
  return REPORT_SOURCE_LABELS[normalized] || source;
}

function parseTimestamp(value?: string | null) {
  if (!value) {
    return 0;
  }

  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

async function downloadArchivedReportPdf(
  reportId: string,
  filename: string
) {
  const response = await apiFetch(
    `/field-reports/visits/${reportId}/pdf`
  );

  if (!response.ok) {
    throw new Error("הורדת ה-PDF נכשלה");
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename || `${reportId}.pdf`;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}

function DocumentTypeBadge({
  kind,
}: {
  kind: "field" | "upload";
}) {
  return (
    <span
      className={
        kind === "field"
          ? "rounded-full bg-brand/10 px-3 py-1 text-xs font-medium text-brand dark:bg-brand/20 dark:text-brand-light"
          : "rounded-full bg-violet-100 px-3 py-1 text-xs font-medium text-violet-700 dark:bg-violet-950/40 dark:text-violet-300"
      }
    >
      {kind === "field" ? "דוח שטח" : "העלאת AI"}
    </span>
  );
}

export default function ProjectDocumentsArchive({
  projectId,
}: Props) {
  const { isEnabled: fieldReportsEnabled, loading: moduleLoading } =
    useFieldReportModule();

  const [filter, setFilter] = useState<DocumentFilter>("all");
  const [fieldArchive, setFieldArchive] =
    useState<FieldReportArchive | null>(null);
  const [uploadArchive, setUploadArchive] =
    useState<UploadedReportsArchive | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [expandedUploadId, setExpandedUploadId] = useState<string | null>(
    null
  );
  const [openYears, setOpenYears] = useState<Record<number, boolean>>({});
  const [openMonths, setOpenMonths] = useState<Record<string, boolean>>({});

  const loadArchive = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const requests: Promise<Response>[] = [
        apiFetch(`/projects/${projectId}/reports/uploads`),
      ];

      if (fieldReportsEnabled) {
        requests.push(
          apiFetch(`/projects/${projectId}/field-reports/archive`)
        );
      }

      const [uploadsResponse, fieldResponse] = await Promise.all(requests);

      if (!uploadsResponse.ok) {
        throw new Error("טעינת מסמכי הפרויקט נכשלה");
      }

      const uploadsPayload =
        (await uploadsResponse.json()) as UploadedReportsArchive;
      setUploadArchive(uploadsPayload);

      if (fieldReportsEnabled) {
        if (!fieldResponse?.ok) {
          throw new Error("טעינת מסמכי הפרויקט נכשלה");
        }

        const fieldPayload =
          (await fieldResponse.json()) as FieldReportArchive;
        setFieldArchive(fieldPayload);

        const defaultOpenYears: Record<number, boolean> = {};
        const defaultOpenMonths: Record<string, boolean> = {};

        if (fieldPayload.years[0]) {
          defaultOpenYears[fieldPayload.years[0].year] = true;
          const firstMonth = fieldPayload.years[0].months[0];
          if (firstMonth) {
            defaultOpenMonths[
              `${fieldPayload.years[0].year}-${firstMonth.month}`
            ] = true;
          }
        }

        setOpenYears(defaultOpenYears);
        setOpenMonths(defaultOpenMonths);
      } else {
        setFieldArchive(null);
      }
    } catch (err: unknown) {
      setFieldArchive(null);
      setUploadArchive(null);
      setError(
        err instanceof Error
          ? err.message
          : "טעינת מסמכי הפרויקט נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, [fieldReportsEnabled, projectId]);

  useEffect(() => {
    if (moduleLoading) {
      return;
    }

    void loadArchive();
  }, [loadArchive, moduleLoading]);

  const fieldReports = useMemo(() => {
    if (!fieldArchive) {
      return [] as ArchivedFieldReport[];
    }

    return fieldArchive.years.flatMap((year) =>
      year.months.flatMap((month) => month.reports)
    );
  }, [fieldArchive]);

  const totalDocuments =
    (fieldArchive?.total_reports ?? 0) + (uploadArchive?.total_reports ?? 0);

  const unifiedDocuments = useMemo(() => {
    const items: Array<
      | {
          kind: "field";
          id: string;
          sortDate: number;
          report: ArchivedFieldReport;
        }
      | {
          kind: "upload";
          id: string;
          sortDate: number;
          report: UploadedReport;
        }
    > = [];

    for (const report of fieldReports) {
      items.push({
        kind: "field",
        id: report.id,
        sortDate: parseTimestamp(report.visit_date),
        report,
      });
    }

    for (const report of uploadArchive?.reports ?? []) {
      items.push({
        kind: "upload",
        id: report.id,
        sortDate: parseTimestamp(report.created_at),
        report,
      });
    }

    return items.sort((left, right) => right.sortDate - left.sortDate);
  }, [fieldReports, uploadArchive?.reports]);

  const filteredUnifiedDocuments = useMemo(() => {
    if (filter === "all") {
      return unifiedDocuments;
    }

    if (filter === "field") {
      return unifiedDocuments.filter((item) => item.kind === "field");
    }

    return unifiedDocuments.filter((item) => item.kind === "upload");
  }, [filter, unifiedDocuments]);

  async function handleDownload(report: ArchivedFieldReport) {
    try {
      setDownloadingId(report.id);
      await downloadArchivedReportPdf(report.id, report.pdf_filename);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "הורדת ה-PDF נכשלה"
      );
    } finally {
      setDownloadingId(null);
    }
  }

  if (moduleLoading) {
    return null;
  }

  return (
    <div className="of-card of-card-p10 of-card-xl mt-10">
      <div className="mb-8">
        <h2 className="text-3xl font-bold">ארכיון מסמכי הפרויקט</h2>
        <p className="mt-3 text-zinc-500">
          כל המסמכים והדוחות של הפרויקט במקום אחד — דוחות שטח שנשלחו
          לליבה (PDF להורדה) ודוחות שהועלו לניתוח AI (תקציר טקסט).
        </p>
      </div>

      <div className="mb-8 flex flex-wrap gap-2">
        {FILTER_OPTIONS.map((option) => {
          const count =
            option.id === "all"
              ? totalDocuments
              : option.id === "field"
                ? fieldArchive?.total_reports ?? 0
                : uploadArchive?.total_reports ?? 0;

          if (option.id === "field" && !fieldReportsEnabled) {
            return null;
          }

          const isActive = filter === option.id;

          return (
            <button
              key={option.id}
              type="button"
              onClick={() => setFilter(option.id)}
              className={
                isActive
                  ? "rounded-full bg-brand px-4 py-2 text-sm font-medium text-white"
                  : "rounded-full border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-600 transition hover:border-brand/40 dark:border-zinc-700 dark:text-zinc-300"
              }
            >
              {option.label}
              {" "}
              ({count})
            </button>
          );
        })}
      </div>

      {loading ? (
        <LoadingState message="טוען ארכיון מסמכים..." />
      ) : error ? (
        <div className="space-y-3">
          <p className="text-sm text-red-600">{error}</p>
          <Button variant="secondary" onClick={() => void loadArchive()}>
            נסה שוב
          </Button>
        </div>
      ) : totalDocuments === 0 ? (
        <div className="rounded-2xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
          <p className="text-sm text-zinc-600">
            עדיין אין מסמכים בפרויקט זה.
          </p>
          <p className="mt-2 text-xs text-zinc-500">
            העלה דוח מדף «העלאת דוח», או שלח דוח שטח לליבה — והם יופיעו כאן.
          </p>
        </div>
      ) : filter === "field" && fieldReportsEnabled ? (
        <FieldReportsSection
          archive={fieldArchive}
          openYears={openYears}
          openMonths={openMonths}
          downloadingId={downloadingId}
          onToggleYear={(year, open) =>
            setOpenYears((current) => ({ ...current, [year]: open }))
          }
          onToggleMonth={(monthKey, open) =>
            setOpenMonths((current) => ({ ...current, [monthKey]: open }))
          }
          onDownload={(report) => void handleDownload(report)}
        />
      ) : filter === "upload" ? (
        <UploadedReportsSection
          reports={uploadArchive?.reports ?? []}
          expandedUploadId={expandedUploadId}
          onToggleExpanded={(reportId) =>
            setExpandedUploadId((current) =>
              current === reportId ? null : reportId
            )
          }
        />
      ) : (
        <UnifiedDocumentsList
          items={filteredUnifiedDocuments}
          downloadingId={downloadingId}
          expandedUploadId={expandedUploadId}
          onDownload={(report) => void handleDownload(report)}
          onToggleExpanded={(reportId) =>
            setExpandedUploadId((current) =>
              current === reportId ? null : reportId
            )
          }
        />
      )}
    </div>
  );
}

type UnifiedDocumentsListProps = {
  items: Array<
    | {
        kind: "field";
        id: string;
        report: ArchivedFieldReport;
      }
    | {
        kind: "upload";
        id: string;
        report: UploadedReport;
      }
  >;
  downloadingId: string | null;
  expandedUploadId: string | null;
  onDownload: (report: ArchivedFieldReport) => void;
  onToggleExpanded: (reportId: string) => void;
};

function UnifiedDocumentsList({
  items,
  downloadingId,
  expandedUploadId,
  onDownload,
  onToggleExpanded,
}: UnifiedDocumentsListProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
        <p className="text-sm text-zinc-600">אין מסמכים בסינון הנוכחי.</p>
      </div>
    );
  }

  return (
    <ul className="divide-y divide-zinc-200 rounded-2xl border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
      {items.map((item) => {
        if (item.kind === "field") {
          const report = item.report;

          return (
            <li
              key={`field-${report.id}`}
              className="flex flex-wrap items-start justify-between gap-3 px-5 py-4"
            >
              <div className="space-y-2">
                <DocumentTypeBadge kind="field" />
                <div>
                  <p className="font-medium">{report.visit_type_label_he}</p>
                  <p className="mt-1 text-sm text-zinc-500">
                    {formatDate(report.visit_date)}
                    {" · "}
                    {report.pdf_filename}
                  </p>
                </div>
              </div>

              <Button
                variant="secondary"
                size="sm"
                disabled={downloadingId === report.id}
                onClick={() => onDownload(report)}
              >
                {downloadingId === report.id ? "מוריד..." : "הורד PDF"}
              </Button>
            </li>
          );
        }

        const report = item.report;
        const isExpanded = expandedUploadId === report.id;
        const hasPreview = Boolean(report.text_preview?.trim());

        return (
          <li key={`upload-${report.id}`} className="px-5 py-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-2">
                <DocumentTypeBadge kind="upload" />
                <div>
                  <p className="font-medium">{report.title}</p>
                  <p className="mt-1 text-sm text-zinc-500">
                    {formatDateTime(report.created_at)}
                    {" · "}
                    סיווג: {getReportSourceLabel(report.report_source)}
                  </p>
                </div>
              </div>

              <Button
                variant="secondary"
                size="sm"
                disabled={!hasPreview}
                onClick={() => onToggleExpanded(report.id)}
              >
                {!hasPreview
                  ? "אין תקציר"
                  : isExpanded
                    ? "הסתר תקציר"
                    : "צפה בתקציר"}
              </Button>
            </div>

            {isExpanded && hasPreview ? (
              <UploadPreviewPanel report={report} />
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

type FieldReportsSectionProps = {
  archive: FieldReportArchive | null;
  openYears: Record<number, boolean>;
  openMonths: Record<string, boolean>;
  downloadingId: string | null;
  onToggleYear: (year: number, open: boolean) => void;
  onToggleMonth: (monthKey: string, open: boolean) => void;
  onDownload: (report: ArchivedFieldReport) => void;
};

function FieldReportsSection({
  archive,
  openYears,
  openMonths,
  downloadingId,
  onToggleYear,
  onToggleMonth,
  onDownload,
}: FieldReportsSectionProps) {
  if (!archive || archive.total_reports === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
        <p className="text-sm text-zinc-600">אין דוחות שטח בארכיון.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {archive.years.map((yearGroup) => {
        const yearOpen = openYears[yearGroup.year] ?? false;

        return (
          <details
            key={yearGroup.year}
            className="rounded-2xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
            open={yearOpen}
            onToggle={(event) => {
              onToggleYear(yearGroup.year, event.currentTarget.open);
            }}
          >
            <summary className="cursor-pointer list-none px-5 py-4 text-xl font-bold">
              {yearGroup.year}
            </summary>

            <div className="space-y-3 border-t border-zinc-200 px-4 py-4 dark:border-zinc-800">
              {yearGroup.months.map((monthGroup) => {
                const monthKey = `${yearGroup.year}-${monthGroup.month}`;
                const monthOpen = openMonths[monthKey] ?? false;

                return (
                  <details
                    key={monthKey}
                    className="rounded-xl border border-zinc-200 dark:border-zinc-800"
                    open={monthOpen}
                    onToggle={(event) => {
                      onToggleMonth(monthKey, event.currentTarget.open);
                    }}
                  >
                    <summary className="cursor-pointer list-none px-4 py-3 font-semibold">
                      {monthGroup.month_label_he}{" "}
                      <span className="text-sm font-normal text-zinc-500">
                        ({monthGroup.reports.length} דוחות)
                      </span>
                    </summary>

                    <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
                      {monthGroup.reports.map((report) => (
                        <li
                          key={report.id}
                          className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
                        >
                          <div>
                            <p className="font-medium">
                              {report.visit_type_label_he}
                            </p>
                            <p className="text-sm text-zinc-500">
                              {formatDate(report.visit_date)}
                              {" · "}
                              {report.pdf_filename}
                            </p>
                          </div>

                          <Button
                            variant="secondary"
                            size="sm"
                            disabled={downloadingId === report.id}
                            onClick={() => onDownload(report)}
                          >
                            {downloadingId === report.id
                              ? "מוריד..."
                              : "הורד PDF"}
                          </Button>
                        </li>
                      ))}
                    </ul>
                  </details>
                );
              })}
            </div>
          </details>
        );
      })}
    </div>
  );
}

type UploadedReportsSectionProps = {
  reports: UploadedReport[];
  expandedUploadId: string | null;
  onToggleExpanded: (reportId: string) => void;
};

function UploadedReportsSection({
  reports,
  expandedUploadId,
  onToggleExpanded,
}: UploadedReportsSectionProps) {
  if (reports.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
        <p className="text-sm text-zinc-600">אין העלאות AI בארכיון.</p>
      </div>
    );
  }

  return (
    <ul className="divide-y divide-zinc-200 rounded-2xl border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
      {reports.map((report) => {
        const isExpanded = expandedUploadId === report.id;
        const hasPreview = Boolean(report.text_preview?.trim());

        return (
          <li key={report.id} className="px-5 py-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-medium">{report.title}</p>
                <p className="mt-1 text-sm text-zinc-500">
                  {formatDateTime(report.created_at)}
                  {" · "}
                  סיווג: {getReportSourceLabel(report.report_source)}
                </p>
              </div>

              <Button
                variant="secondary"
                size="sm"
                disabled={!hasPreview}
                onClick={() => onToggleExpanded(report.id)}
              >
                {!hasPreview
                  ? "אין תקציר"
                  : isExpanded
                    ? "הסתר תקציר"
                    : "צפה בתקציר"}
              </Button>
            </div>

            {isExpanded && hasPreview ? (
              <UploadPreviewPanel report={report} />
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

function UploadPreviewPanel({ report }: { report: UploadedReport }) {
  return (
    <div className="mt-4 space-y-4 rounded-2xl bg-zinc-50 p-4 dark:bg-zinc-900/50">
      <div>
        <h3 className="mb-2 text-sm font-semibold">תקציר טקסט מהדוח</h3>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          {report.text_preview}
        </p>
      </div>

      {report.recommended_action ? (
        <div>
          <h3 className="mb-2 text-sm font-semibold">פעולה מומלצת</h3>
          <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
            {report.recommended_action}
          </p>
        </div>
      ) : null}

      <p className="text-xs text-zinc-500">
        הקובץ המקורי שהועלה אינו זמין להורדה — המערכת שומרת את תוצאות
        הניתוח בלבד.
      </p>
    </div>
  );
}
