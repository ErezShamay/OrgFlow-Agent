"use client";

import { useCallback, useEffect, useState } from "react";

import Button from "@/components/ui/Button";
import LoadingState from "@/components/ui/LoadingState";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { apiFetch } from "@/lib/api/client";

type ArchivedReport = {
  id: string;
  visit_date: string;
  visit_type_label_he: string;
  pdf_filename: string;
  locked_at?: string | null;
};

type ArchiveMonth = {
  month: number;
  month_label_he: string;
  reports: ArchivedReport[];
};

type ArchiveYear = {
  year: number;
  months: ArchiveMonth[];
};

type ProjectFieldReportArchive = {
  project_id: string;
  project_name?: string | null;
  years: ArchiveYear[];
  total_reports: number;
};

type Props = {
  projectId: string;
};

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

function formatVisitDate(value: string) {
  try {
    return new Date(value).toLocaleDateString("he-IL");
  } catch {
    return value;
  }
}

export default function ProjectReportsArchive({
  projectId,
}: Props) {
  const { isEnabled, loading: moduleLoading } = useFieldReportModule();
  const [archive, setArchive] =
    useState<ProjectFieldReportArchive | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [downloadingId, setDownloadingId] = useState<string | null>(
    null
  );
  const [openYears, setOpenYears] = useState<Record<number, boolean>>(
    {}
  );
  const [openMonths, setOpenMonths] = useState<Record<string, boolean>>(
    {}
  );

  const loadArchive = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await apiFetch(
        `/projects/${projectId}/field-reports/archive`
      );

      if (!response.ok) {
        throw new Error("טעינת ארכיון הדוחות נכשלה");
      }

      const payload =
        (await response.json()) as ProjectFieldReportArchive;
      setArchive(payload);

      const defaultOpenYears: Record<number, boolean> = {};
      const defaultOpenMonths: Record<string, boolean> = {};

      if (payload.years[0]) {
        defaultOpenYears[payload.years[0].year] = true;
        const firstMonth = payload.years[0].months[0];
        if (firstMonth) {
          defaultOpenMonths[
            `${payload.years[0].year}-${firstMonth.month}`
          ] = true;
        }
      }

      setOpenYears(defaultOpenYears);
      setOpenMonths(defaultOpenMonths);
    } catch (err: unknown) {
      setArchive(null);
      setError(
        err instanceof Error
          ? err.message
          : "טעינת ארכיון הדוחות נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (!isEnabled || moduleLoading) {
      return;
    }

    void loadArchive();
  }, [isEnabled, moduleLoading, loadArchive]);

  async function handleDownload(report: ArchivedReport) {
    try {
      setDownloadingId(report.id);
      await downloadArchivedReportPdf(
        report.id,
        report.pdf_filename
      );
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "הורדת ה-PDF נכשלה"
      );
    } finally {
      setDownloadingId(null);
    }
  }

  if (moduleLoading) {
    return null;
  }

  if (!isEnabled) {
    return null;
  }

  return (
    <div className="of-card of-card-p10 of-card-xl mt-10">
      <div className="mb-8">
        <h2 className="text-3xl font-bold">ארכיון דוחות מקוריים</h2>
        <p className="mt-3 text-zinc-500">
          כל דוח PDF שהופק ונשלח לליבה נשמר לצמיתות תחת הפרויקט —
          לפי שנה וחודש.
        </p>
      </div>

      {loading ? (
        <LoadingState message="טוען ארכיון דוחות..." />
      ) : error ? (
        <div className="space-y-3">
          <p className="text-sm text-red-600">{error}</p>
          <Button variant="secondary" onClick={() => void loadArchive()}>
            נסה שוב
          </Button>
        </div>
      ) : !archive || archive.total_reports === 0 ? (
        <div className="rounded-2xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
          <p className="text-sm text-zinc-600">
            עדיין אין דוחות PDF בארכיון הפרויקט.
          </p>
          <p className="mt-2 text-xs text-zinc-500">
            דוחות יופיעו כאן לאחר שליחה מוצלחת לליבה.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-zinc-500">
            {archive.total_reports} דוחות בארכיון
          </p>

          {archive.years.map((yearGroup) => {
            const yearOpen = openYears[yearGroup.year] ?? false;

            return (
              <details
                key={yearGroup.year}
                className="rounded-2xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
                open={yearOpen}
                onToggle={(event) => {
                  setOpenYears((current) => ({
                    ...current,
                    [yearGroup.year]: event.currentTarget.open,
                  }));
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
                          setOpenMonths((current) => ({
                            ...current,
                            [monthKey]: event.currentTarget.open,
                          }));
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
                                  {formatVisitDate(report.visit_date)}
                                  {" · "}
                                  {report.pdf_filename}
                                </p>
                              </div>

                              <Button
                                variant="secondary"
                                size="sm"
                                disabled={downloadingId === report.id}
                                onClick={() => void handleDownload(report)}
                              >
                                {downloadingId === report.id
                                  ? "מוריד..."
                                  : "הורד PDF מקורי"}
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
      )}
    </div>
  );
}
