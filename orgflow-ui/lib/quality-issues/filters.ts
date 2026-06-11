import {
  isContractorIssuesView,
} from "@/lib/quality-issues/contractor-issues-view";
import { visibleIssueStatusesForRole } from "@/lib/quality-issues/permissions";
import {
  QUALITY_ISSUE_SEVERITIES,
  QUALITY_ISSUE_STATUSES,
  type QualityIssueListQuery,
  type QualityIssueSeverity,
  type QualityIssueStatus,
} from "@/lib/quality-issues/types";

export type IssuesFilterState = {
  status: QualityIssueStatus | "";
  severity: QualityIssueSeverity | "";
  trade: string;
};

export function createEmptyIssuesFilterState(): IssuesFilterState {
  return {
    status: "",
    severity: "",
    trade: "",
  };
}

export function availableStatusFilterOptions(
  role?: string | null
): QualityIssueStatus[] {
  const visible = visibleIssueStatusesForRole(role);
  if (visible === null) {
    return [...QUALITY_ISSUE_STATUSES];
  }

  return QUALITY_ISSUE_STATUSES.filter((status) => visible.has(status));
}

export function issuesFilterStateToListQuery(
  filters: IssuesFilterState,
  role?: string | null
): QualityIssueListQuery {
  const query: QualityIssueListQuery = {};
  const trade = filters.trade.trim();

  if (filters.status) {
    query.status = [filters.status];
  }
  if (filters.severity) {
    query.severity = [filters.severity];
  }
  if (trade) {
    query.trade = trade;
  }

  const visible = visibleIssueStatusesForRole(role);
  if (visible === null) {
    return query;
  }

  const visibleStatuses = [...visible];
  if (query.status?.length) {
    const allowed = query.status.filter((status) => visible.has(status));
    return {
      ...query,
      status: allowed.length > 0 ? allowed : visibleStatuses,
    };
  }

  return {
    ...query,
    status: visibleStatuses,
  };
}

export function serializeIssuesFilterKey(
  filters: IssuesFilterState,
  role?: string | null
): string {
  const personaKey = isContractorIssuesView(role) ? "contractor" : "all";
  const visibleKey =
    visibleIssueStatusesForRole(role) === null
      ? "all-statuses"
      : availableStatusFilterOptions(role)
          .slice()
          .sort()
          .join("+");

  return [
    personaKey,
    visibleKey,
    filters.status || "_",
    filters.severity || "_",
    filters.trade.trim().toLowerCase(),
  ].join("|");
}

export function hasActiveIssuesFilters(filters: IssuesFilterState): boolean {
  return Boolean(
    filters.status || filters.severity || filters.trade.trim()
  );
}
