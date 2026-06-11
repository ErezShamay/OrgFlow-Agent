import type { QualityPortfolioSummaryResponse } from "@/lib/quality-issues/types";

export const CRITICAL_STALE_DAYS_THRESHOLD = 14;
export const CLOSED_WITHIN_DAYS_THRESHOLD = 30;
export const CLOSED_WITHIN_DAYS_HEALTHY_PERCENT = 80;
export const AVERAGE_OPEN_DAYS_HEALTHY_THRESHOLD = 14;

export function formatAverageOpenDays(value: number | null | undefined): string {
  if (value == null) {
    return "-";
  }

  return `${value} ימים`;
}

export function formatAverageOpenDaysCaption(
  summary: Pick<QualityPortfolioSummaryResponse, "average_open_days" | "total_open">
): string {
  if (summary.total_open === 0 || summary.average_open_days == null) {
    return "אין ליקויים פתוחים לחישוב ממוצע ימים";
  }

  return `ממוצע ${summary.average_open_days} ימים פתוח לליקוי (${summary.total_open} פתוחים)`;
}

export function isAverageOpenDaysHealthy(
  value: number | null | undefined
): boolean {
  return value != null && value <= AVERAGE_OPEN_DAYS_HEALTHY_THRESHOLD;
}

export function formatClosedWithin30DaysPercent(value: number | null): string {
  if (value == null) {
    return "-";
  }

  return `${value}%`;
}

export function formatClosedWithin30DaysCaption(
  summary: Pick<QualityPortfolioSummaryResponse, "closed_within_30_days_percent">
): string {
  if (summary.closed_within_30_days_percent == null) {
    return "אין ליקויים סגורים לחישוב אחוז סגירה";
  }

  return `${summary.closed_within_30_days_percent}% מהליקויים הסגורים נסגרו תוך ${CLOSED_WITHIN_DAYS_THRESHOLD} יום`;
}

export function isClosedWithin30DaysHealthy(
  value: number | null
): boolean {
  return value != null && value >= CLOSED_WITHIN_DAYS_HEALTHY_PERCENT;
}

export function formatCriticalOpenOver14DaysCaption(
  summary: Pick<
    QualityPortfolioSummaryResponse,
    "critical_open_over_14_days" | "total_open_critical"
  >
): string {
  if (summary.critical_open_over_14_days === 0) {
    return "אין ליקויים קריטיים פתוחים מעל 14 יום";
  }

  return `${summary.critical_open_over_14_days} ליקויים קריטיים פתוחים מעל ${CRITICAL_STALE_DAYS_THRESHOLD} יום`;
}

export function countProjectsWithStaleCriticalIssues(
  projects: QualityPortfolioSummaryResponse["projects"]
): number {
  return projects.filter(
    (project) => project.critical_open_over_14_days > 0
  ).length;
}

export function countProjectsWithOpenIssues(
  projects: QualityPortfolioSummaryResponse["projects"]
): number {
  return projects.filter((project) => project.open_total > 0).length;
}

export function formatOpenIssuesPerProjectCaption(
  projects: QualityPortfolioSummaryResponse["projects"]
): string {
  const withOpenIssues = countProjectsWithOpenIssues(projects);
  const totalProjects = projects.length;

  if (totalProjects === 0) {
    return "אין פרויקטים בתיק";
  }

  return `${withOpenIssues} פרויקטים עם ליקויים פתוחים מתוך ${totalProjects}`;
}

export function openIssuesPerProjectRows(
  projects: QualityPortfolioSummaryResponse["projects"]
): QualityPortfolioSummaryResponse["projects"] {
  return [...projects];
}

export function rankProjectsByQcPressure(
  projects: QualityPortfolioSummaryResponse["projects"]
): QualityPortfolioSummaryResponse["projects"] {
  return [...projects].sort((left, right) => {
    if (right.open_critical !== left.open_critical) {
      return right.open_critical - left.open_critical;
    }

    if (right.open_total !== left.open_total) {
      return right.open_total - left.open_total;
    }

    return (left.project_name ?? "").localeCompare(
      right.project_name ?? "",
      "he"
    );
  });
}

/** @deprecated Use rankProjectsByQcPressure - kept for existing imports. */
export function sortProjectsByOpenCritical(
  projects: QualityPortfolioSummaryResponse["projects"]
): QualityPortfolioSummaryResponse["projects"] {
  return rankProjectsByQcPressure(projects);
}

export function countProjectsWithOpenCritical(
  projects: QualityPortfolioSummaryResponse["projects"]
): number {
  return projects.filter((project) => project.open_critical > 0).length;
}

export function formatProjectQcRankCaption(
  projects: QualityPortfolioSummaryResponse["projects"]
): string {
  const withCritical = countProjectsWithOpenCritical(projects);
  const withOpen = countProjectsWithOpenIssues(projects);
  const totalProjects = projects.length;

  if (totalProjects === 0) {
    return "אין פרויקטים לדירוג";
  }

  return `${withCritical} פרויקטים עם ליקויים קריטיים, ${withOpen} עם ליקויים פתוחים - מתוך ${totalProjects}`;
}

export function projectQcPressureLevel(
  project: QualityPortfolioSummaryResponse["projects"][number]
): "critical" | "open" | "clear" {
  if (project.open_critical > 0) {
    return "critical";
  }

  if (project.open_total > 0) {
    return "open";
  }

  return "clear";
}
