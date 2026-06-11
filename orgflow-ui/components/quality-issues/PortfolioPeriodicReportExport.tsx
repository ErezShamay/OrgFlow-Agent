"use client";

import { useCallback, useState } from "react";

import Button from "@/components/ui/Button";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { getPortfolioPeriodicReport } from "@/lib/quality-issues/api";
import {
  buildPeriodicReportCsv,
  buildPeriodicReportCsvFilename,
  DEFAULT_PERIODIC_REPORT_DAYS,
  downloadPeriodicReportPdf,
  downloadTextFile,
  formatPeriodicReportPeriod,
} from "@/lib/quality-issues/periodic-report";
import { hasQCPermission } from "@/lib/quality-issues/permissions";

export default function PortfolioPeriodicReportExport() {
  const effectiveRole = useEffectiveRole();
  const canReadPortfolio = hasQCPermission(
    effectiveRole,
    "quality_portfolio:read"
  );
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);

  const loadReport = useCallback(async () => {
    return getPortfolioPeriodicReport(DEFAULT_PERIODIC_REPORT_DAYS);
  }, []);

  const { data: report, loading, error } = useOrgQuery(
    "portfolio/quality-periodic-report",
    loadReport,
    {
      enabled: canReadPortfolio,
      showErrorToast: false,
    }
  );

  if (!canReadPortfolio) {
    return null;
  }

  const handleCsvExport = async () => {
    if (!report) {
      return;
    }

    setExporting("csv");
    try {
      downloadTextFile(
        buildPeriodicReportCsv(report),
        buildPeriodicReportCsvFilename(report),
        "text/csv;charset=utf-8"
      );
    } finally {
      setExporting(null);
    }
  };

  const handlePdfExport = async () => {
    if (!report) {
      return;
    }

    setExporting("pdf");
    try {
      await downloadPeriodicReportPdf(report);
    } finally {
      setExporting(null);
    }
  };

  return (
    <section className="mb-10 space-y-4">
      <div className="space-y-1">
        <p className="text-zinc-500">דוחות</p>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          דוח תקופתי ליזם
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {report
            ? `תקופה: ${formatPeriodicReportPeriod(report)} · ${report.summary.total_issues} ליקויים`
            : "סיכום QC ל-30 יום - ייצוא Excel (CSV) או PDF"}
        </p>
      </div>

      {error ? (
        <div className="of-card of-card-p8 text-sm text-red-600 dark:text-red-400">
          {error.message}
        </div>
      ) : (
        <div className="of-card of-card-p8 flex flex-wrap items-center gap-3">
          <Button
            type="button"
            variant="secondary"
            disabled={loading || !report || exporting !== null}
            onClick={handleCsvExport}
          >
            {exporting === "csv" ? "מייצא..." : "ייצוא Excel (CSV)"}
          </Button>
          <Button
            type="button"
            disabled={loading || !report || exporting !== null}
            onClick={handlePdfExport}
          >
            {exporting === "pdf" ? "מייצא..." : "ייצוא PDF"}
          </Button>
        </div>
      )}
    </section>
  );
}
