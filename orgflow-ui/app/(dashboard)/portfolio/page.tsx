"use client";

import PortfolioLegacySection from "@/components/quality-issues/PortfolioLegacySection";
import PortfolioPeriodicReportExport from "@/components/quality-issues/PortfolioPeriodicReportExport";
import PortfolioProjectRanking from "@/components/quality-issues/PortfolioProjectRanking";
import PortfolioQualitySummaryPanel from "@/components/quality-issues/PortfolioQualitySummaryPanel";
import PortfolioRecurringRankingsPanel from "@/components/quality-issues/PortfolioRecurringRankingsPanel";
import PortfolioTradeHeatmapPanel from "@/components/quality-issues/PortfolioTradeHeatmapPanel";
import {
  PORTFOLIO_QC_PAGE_EYEBROW,
  PORTFOLIO_QC_PAGE_SUBTITLE,
  PORTFOLIO_QC_PAGE_TITLE,
} from "@/lib/quality-issues/portfolio-page";

export default function PortfolioPage() {
  return (
    <main className="of-dashboard-page">
      <header className="mb-10 space-y-2">
        <p className="text-zinc-500">{PORTFOLIO_QC_PAGE_EYEBROW}</p>
        <h1 className="of-page-title">{PORTFOLIO_QC_PAGE_TITLE}</h1>
        <p className="max-w-3xl text-sm text-zinc-600 dark:text-zinc-400">
          {PORTFOLIO_QC_PAGE_SUBTITLE}
        </p>
      </header>

      <PortfolioQualitySummaryPanel />
      <PortfolioTradeHeatmapPanel />
      <PortfolioRecurringRankingsPanel />
      <PortfolioPeriodicReportExport />
      <PortfolioProjectRanking />
      <PortfolioLegacySection />
    </main>
  );
}
