"use client";

import Link from "next/link";

import Badge from "@/components/ui/Badge";
import {
  projectApartmentPortalPath,
  projectSupervisionPublicAreaVisitReportPath,
  projectSupervisionVisitReportPath,
} from "@/lib/projects/supervision-dashboard";
import type {
  SupervisionApartmentProgress,
  SupervisionPublicAreaProgress,
} from "@/lib/projects/supervision-dashboard-types";

type GridUnit =
  | ({ kind: "apartment" } & SupervisionApartmentProgress)
  | ({ kind: "public_area" } & SupervisionPublicAreaProgress);

type ProjectApartmentProgressGridProps = {
  projectId: string;
  apartments: SupervisionApartmentProgress[];
  publicAreas?: SupervisionPublicAreaProgress[];
};

function buildGridUnits(
  apartments: SupervisionApartmentProgress[],
  publicAreas: SupervisionPublicAreaProgress[]
): GridUnit[] {
  const apartmentUnits: GridUnit[] = apartments.map((apartment) => ({
    kind: "apartment",
    ...apartment,
  }));
  const publicUnits: GridUnit[] = publicAreas.map((area) => ({
    kind: "public_area",
    ...area,
  }));
  return [...apartmentUnits, ...publicUnits];
}

function unitLabel(unit: GridUnit): string {
  if (unit.kind === "apartment") {
    return `דירה ${unit.apartment_number}`;
  }
  return unit.label_he;
}

function unitIssuesCount(unit: GridUnit): number {
  return unit.open_issues_count;
}

function unitPortalHref(projectId: string, unit: GridUnit): string | null {
  if (unit.kind === "apartment" && unit.apartment_id) {
    return projectApartmentPortalPath(projectId, unit.apartment_id);
  }
  return null;
}

function unitVisitHref(projectId: string, unit: GridUnit): string | null {
  if (unit.kind === "apartment") {
    return projectSupervisionVisitReportPath(
      projectId,
      unit.apartment_number,
      unit.apartment_id
    );
  }
  return projectSupervisionPublicAreaVisitReportPath(projectId, unit.area_key);
}

export default function ProjectApartmentProgressGrid({
  projectId,
  apartments,
  publicAreas = [],
}: ProjectApartmentProgressGridProps) {
  const units = buildGridUnits(apartments, publicAreas);

  return (
    <section className="of-card of-card-p6 shadow-sm" dir="rtl">
      <h2 className="mb-6 text-xl font-bold text-zinc-900 dark:text-zinc-100">
        התקדמות לפי דירה ואזורים
      </h2>

      {units.length === 0 ? (
        <p className="text-sm text-zinc-500">
          אין עדיין דירות או אזורים ציבוריים עם ביקורי פיקוח מתועדים.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {units.map((unit) => {
            const portalHref = unitPortalHref(projectId, unit);
            const visitHref = unitVisitHref(projectId, unit);
            const issuesCount = unitIssuesCount(unit);
            const cardKey =
              unit.kind === "apartment"
                ? `apt-${unit.apartment_number}`
                : `area-${unit.area_key}`;

            const cardBody = (
              <>
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                    {unitLabel(unit)}
                  </h3>
                  <span
                    className="text-sm font-bold text-zinc-700 dark:text-zinc-200"
                    dir="ltr"
                  >
                    {unit.progress_percent}%
                  </span>
                </div>

                <div
                  className="mt-3 h-2 overflow-hidden rounded-full bg-zinc-200/80 dark:bg-zinc-700"
                  role="progressbar"
                  aria-valuenow={unit.progress_percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className="h-full rounded-full bg-brand transition-all"
                    style={{
                      width: `${Math.min(100, Math.max(0, unit.progress_percent))}%`,
                    }}
                  />
                </div>

                <div className="mt-4">
                  {issuesCount > 0 ? (
                    <Badge variant="danger">{issuesCount} ליקויים</Badge>
                  ) : (
                    <Badge variant="success">ללא ליקויים פתוחים</Badge>
                  )}
                </div>

                {visitHref ? (
                  <div className="mt-4" onClick={(event) => event.stopPropagation()}>
                    <Link
                      href={visitHref}
                      className="of-focus-ring inline-flex w-full items-center justify-center rounded-xl bg-brand px-3 py-1.5 text-sm font-semibold text-white transition-all hover:bg-brand-dark dark:bg-brand-light dark:text-brand-dark dark:hover:bg-brand"
                    >
                      תיעוד ביקור
                    </Link>
                  </div>
                ) : null}
              </>
            );

            if (portalHref) {
              return (
                <Link
                  key={cardKey}
                  href={portalHref}
                  className="block rounded-2xl border border-zinc-200/80 bg-white/90 p-5 shadow-sm transition hover:border-brand/30 hover:shadow-md dark:border-zinc-700 dark:bg-zinc-900/80"
                >
                  {cardBody}
                </Link>
              );
            }

            return (
              <article
                key={cardKey}
                className="rounded-2xl border border-zinc-200/80 bg-white/90 p-5 shadow-sm dark:border-zinc-700 dark:bg-zinc-900/80"
              >
                {cardBody}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
