"use client";

import { useState } from "react";

import ConstructionProgressGantt from "@/components/apartments/ConstructionProgressGantt";
import Button from "@/components/ui/Button";
import { downloadResidentPortalPdf } from "@/lib/apartments/api";
import type { ResidentPortalPayload } from "@/lib/apartments/types";
import {
  reportSourceLabel,
  residentStatusLevelEmoji,
  residentStatusLevelLabel,
} from "@/lib/apartments/types";

function splitOwnerName(ownerName: string): {
  firstName: string;
  familyName: string;
} {
  const trimmed = ownerName.trim();
  if (!trimmed) {
    return { firstName: "", familyName: "" };
  }
  const parts = trimmed.split(/\s+/);
  if (parts.length === 1) {
    return { firstName: parts[0], familyName: "" };
  }
  return {
    firstName: parts[0],
    familyName: parts.slice(1).join(" "),
  };
}

type ResidentPortalViewProps = {
  data: ResidentPortalPayload;
  title?: string;
  pitchMode?: boolean;
};

export default function ResidentPortalView({
  data,
  title = "תיק דייר הנדסי",
  pitchMode = false,
}: ResidentPortalViewProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [downloadingReportId, setDownloadingReportId] = useState<string | null>(
    null
  );
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const {
    apartment,
    project_name,
    status_cards,
    pdf_downloads,
    reports,
    report_lines,
    issues,
    progress_timeline,
    gantt_rows,
  } = data;

  const { firstName, familyName } = splitOwnerName(apartment.owner_name ?? "");
  const residentEmail = apartment.email?.trim() || null;

  const handlePdfDownload = async (reportId: string, pdfUrl: string, label: string) => {
    setDownloadingReportId(reportId);
    setDownloadError(null);
    try {
      await downloadResidentPortalPdf(pdfUrl, label);
    } catch (error) {
      setDownloadError(
        error instanceof Error ? error.message : "הורדת ה-PDF נכשלה"
      );
    } finally {
      setDownloadingReportId(null);
    }
  };

  return (
    <div className="of-dashboard-page of-container mx-auto max-w-5xl space-y-8 px-4 pb-10 md:px-0">
      <header className="space-y-3">
        <h1 className="of-page-title text-2xl md:text-3xl">{title}</h1>
        <p className="of-page-desc text-sm">
          דירה {apartment.apartment_number}
          {project_name ? ` · ${project_name}` : ""}
        </p>
        <p className="text-sm text-zinc-600 dark:text-zinc-300">
          {pitchMode
            ? "שקיפות ממותגת — רואים בדיוק על מה אנחנו נלחמים בשטח."
            : "תמונת מצב הנדסית מפורסמת בלבד — ללא טיוטות פנימיות."}
        </p>
        {data.read_only ? (
          <p className="text-xs text-zinc-500">צפייה בלבד — אין אפשרות לערוך נתונים</p>
        ) : null}
      </header>

      <section className="of-card of-card-p6 space-y-3">
        <h2 className="text-lg font-semibold">פרטים אישיים</h2>
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-zinc-500">שם פרטי</dt>
            <dd className="font-medium">{firstName || "—"}</dd>
          </div>
          <div>
            <dt className="text-zinc-500">שם משפחה</dt>
            <dd className="font-medium">{familyName || "—"}</dd>
          </div>
          <div>
            <dt className="text-zinc-500">מייל</dt>
            <dd className="font-medium">{residentEmail || "—"}</dd>
          </div>
          <div>
            <dt className="text-zinc-500">מספר דירה</dt>
            <dd className="font-medium">{apartment.apartment_number}</dd>
          </div>
        </dl>
      </section>

      <section className="of-card of-card-p6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">Trust Dashboard</h2>
          <span className="text-xs text-zinc-500">מידע מפורסם בלבד</span>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {(status_cards ?? []).map((card) => (
            <article
              key={card.card_key}
              className="rounded-2xl border border-zinc-200/80 p-5 dark:border-zinc-700/80"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm text-zinc-500">{card.title}</p>
                  <p className="mt-2 text-2xl font-semibold">
                    {residentStatusLevelEmoji(card.level)}{" "}
                    {residentStatusLevelLabel(card.level)}
                  </p>
                </div>
                <span className="text-xs text-zinc-500">
                  {card.issue_count} ליקויים
                </span>
              </div>
              <dl className="mt-4 grid grid-cols-3 gap-2 text-xs text-zinc-500">
                <div>
                  <dt>פתוחים</dt>
                  <dd className="font-medium text-zinc-800 dark:text-zinc-100">
                    {card.open_count}
                  </dd>
                </div>
                <div>
                  <dt>סגורים</dt>
                  <dd className="font-medium text-zinc-800 dark:text-zinc-100">
                    {card.closed_count}
                  </dd>
                </div>
                <div>
                  <dt>קריטיים</dt>
                  <dd className="font-medium text-zinc-800 dark:text-zinc-100">
                    {card.critical_open_count}
                  </dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="of-card of-card-p6 space-y-4">
        <h2 className="text-lg font-semibold">מרכז הורדות — דוחות PDF</h2>
        {downloadError ? (
          <p className="text-sm text-red-600">{downloadError}</p>
        ) : null}
        {(pdf_downloads ?? []).length === 0 ? (
          <p className="text-sm text-zinc-500">
            אין דוחות PDF מפורסמים לדירה זו עדיין.
          </p>
        ) : (
          <ul className="divide-y divide-zinc-200/80 dark:divide-zinc-700/80">
            {pdf_downloads.map((item) => (
              <li
                key={item.report_id}
                className="flex flex-wrap items-center justify-between gap-3 py-3"
              >
                <div>
                  <p className="font-medium">
                    {item.title || reportSourceLabel(item.source) || "דוח פיקוח"}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {reportSourceLabel(item.source)} · {item.visit_date || "—"}
                  </p>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={downloadingReportId === item.report_id}
                  onClick={() =>
                    void handlePdfDownload(
                      item.report_id,
                      item.pdf_url,
                      item.title || `דוח-${item.report_id}.pdf`
                    )
                  }
                >
                  {downloadingReportId === item.report_id ? "מוריד..." : "הורד PDF"}
                </Button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="of-card of-card-p6 space-y-4">
        <h2 className="text-lg font-semibold">התקדמות מלאכות — לוח גantt</h2>
        <ConstructionProgressGantt rows={gantt_rows ?? []} />
      </section>

      {progress_timeline.length > 0 ? (
        <section className="of-card of-card-p6 space-y-4">
          <h2 className="text-lg font-semibold">פירוט התקדמות</h2>
          <div className="space-y-3">
            {progress_timeline.map((item, index) => (
              <div
                key={`${item.report_id}-${item.description}-${index}`}
                className="rounded-xl border border-zinc-200/80 p-4 dark:border-zinc-700/80"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium">{item.description}</p>
                  <span className="text-xs text-zinc-500">
                    {item.visit_date || item.completion_date || "—"}
                  </span>
                </div>
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
                  סטטוס: {item.status || "—"}
                </p>
                {item.report_title ? (
                  <p className="mt-1 text-xs text-zinc-500">{item.report_title}</p>
                ) : null}
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="of-card of-card-p6 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">פירוט ממצאים וליקויים</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowDetails((current) => !current)}
          >
            {showDetails ? "הסתר פירוט" : "הצג פירוט"}
          </Button>
        </div>
        {!showDetails ? (
          <p className="text-sm text-zinc-500">
            תצוגת ברירת המחדל מציגה סטטוס מרוכז. ניתן לפתוח פירוט לפי צורך.
          </p>
        ) : (
          <div className="space-y-6">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold">דוחות ופרוטוקולים</h3>
              {reports.length === 0 ? (
                <p className="text-sm text-zinc-500">
                  אין דוחות שטח או דוחות שבועיים המשויכים לדירה זו.
                </p>
              ) : (
                <ul className="divide-y divide-zinc-200/80 dark:divide-zinc-700/80">
                  {reports.map((report) => (
                    <li
                      key={report.id}
                      className="flex flex-wrap items-center justify-between gap-2 py-3"
                    >
                      <div>
                        <p className="font-medium">
                          {report.title || report.visit_type || "דוח"}
                        </p>
                        <p className="text-xs text-zinc-500">
                          {reportSourceLabel(report.source)} · {report.visit_date || "—"} ·{" "}
                          {report.line_count} ממצאים
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-semibold">ממצאים ובדיקות בדירה</h3>
              {report_lines.length === 0 ? (
                <p className="text-sm text-zinc-500">אין ממצאים רשומים לדירה זו.</p>
              ) : (
                <ul className="space-y-3">
                  {report_lines.map((line) => (
                    <li
                      key={line.id}
                      className="rounded-xl border border-zinc-200/80 p-3 text-sm dark:border-zinc-700/80"
                    >
                      <p className="font-medium">{line.description || "ממצא"}</p>
                      <p className="text-zinc-500">
                        {line.visit_date || "—"} · {line.status || "—"}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-semibold">ליקויים מפורסמים</h3>
              {issues.length === 0 ? (
                <p className="text-sm text-zinc-500">
                  אין ליקויים מפורסמים לדירה זו.
                </p>
              ) : (
                <ul className="space-y-3">
                  {issues.map((issue) => (
                    <li
                      key={issue.id}
                      className="rounded-xl border border-zinc-200/80 p-3 text-sm dark:border-zinc-700/80"
                    >
                      <p className="font-medium">{issue.title || issue.trade || "ליקוי"}</p>
                      <p className="text-zinc-500">
                        {issue.tenant_view_status_he || issue.status || "—"}
                        {issue.location ? ` · ${issue.location}` : ""}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
