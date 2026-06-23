"use client";

import type { SupervisionDashboardKpis } from "@/lib/projects/supervision-dashboard-types";

type ProjectSupervisionKpiRowProps = {
  kpis: SupervisionDashboardKpis;
};

type KpiTileProps = {
  label: string;
  value: string;
  subtitle?: string;
  tone: "blue" | "orange" | "green" | "slate";
  progressPercent?: number;
};

const TONE_CLASSES: Record<KpiTileProps["tone"], string> = {
  blue: "border-sky-200/80 bg-sky-50/90 dark:border-sky-900/50 dark:bg-sky-950/40",
  orange:
    "border-orange-200/80 bg-orange-50/90 dark:border-orange-900/50 dark:bg-orange-950/40",
  green:
    "border-emerald-200/80 bg-emerald-50/90 dark:border-emerald-900/50 dark:bg-emerald-950/40",
  slate:
    "border-zinc-300/80 bg-zinc-100/90 dark:border-zinc-700 dark:bg-zinc-900/70",
};

const TONE_VALUE_CLASSES: Record<KpiTileProps["tone"], string> = {
  blue: "text-sky-700 dark:text-sky-300",
  orange: "text-orange-700 dark:text-orange-300",
  green: "text-emerald-700 dark:text-emerald-300",
  slate: "text-zinc-900 dark:text-zinc-100",
};

function KpiTile({ label, value, subtitle, tone, progressPercent }: KpiTileProps) {
  return (
    <div
      className={`rounded-2xl border p-5 shadow-sm ${TONE_CLASSES[tone]}`}
      dir="rtl"
    >
      <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
        {label}
      </p>
      <p
        className={`mt-2 text-4xl font-black tracking-tight ${TONE_VALUE_CLASSES[tone]}`}
        dir="ltr"
      >
        {value}
      </p>
      {subtitle ? (
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          {subtitle}
        </p>
      ) : null}
      {typeof progressPercent === "number" ? (
        <div
          className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-200/80 dark:bg-zinc-700"
          role="progressbar"
          aria-valuenow={progressPercent}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-full bg-zinc-800 transition-all dark:bg-zinc-200"
            style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%` }}
          />
        </div>
      ) : null}
    </div>
  );
}

export default function ProjectSupervisionKpiRow({
  kpis,
}: ProjectSupervisionKpiRowProps) {
  return (
    <section
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
      aria-label="מדדי דשבורד פרויקט"
      dir="rtl"
    >
      <KpiTile
        label="בטיפול"
        value={String(kpis.in_treatment)}
        subtitle="פריטים בטיפול"
        tone="blue"
      />
      <KpiTile
        label="עם ליקויים"
        value={String(kpis.with_defects)}
        subtitle="פריטים עם ליקויים"
        tone="orange"
      />
      <KpiTile
        label="הושלמו"
        value={String(kpis.completed)}
        subtitle="פריטים שהושלמו"
        tone="green"
      />
      <KpiTile
        label="התקדמות כללית"
        value={`${kpis.progress_percent}%`}
        subtitle={`מתוך ${kpis.total_items} פריטים`}
        tone="slate"
        progressPercent={kpis.progress_percent}
      />
    </section>
  );
}
