/**
 * Offline cache for open quality issues (roadmap 2.1.7).
 * Populated during field-report offline prep; read without network in the field.
 */

import {
  clearOpenIssuesCacheRecord,
  getProjectOpenIssuesSnapshot,
  isOpenIssuesCacheExpired,
  loadOpenIssuesCacheRecord,
  saveOpenIssuesCacheRecord,
  type OpenIssuesCacheRecord,
} from "@/lib/field-reports/repositories/open-issues-repository";
import { listProjectOpenQualityIssues } from "@/lib/quality-issues/api";
import { findOpenIssueMatches, matchKeyForFinding } from "@/lib/quality-issues/matching";
import {
  isTerminalIssueStatus,
  type FindingMatchInput,
  type QualityIssue,
  type QualityIssueOpenListResponse,
  type QualityIssueStatus,
  type QualityIssueSuggestMatchesResponse,
} from "@/lib/quality-issues/types";

export type { OpenIssuesCacheRecord };

export const OPEN_ISSUES_CACHE_UNAVAILABLE_MESSAGE =
  "אין ליקויים פתוחים מקומיים - בצע «הכנה לא מקוון» כשיש רשת.";

const openIssuesCache = new Map<string, OpenIssuesCacheRecord>();

function setCachedOpenIssuesRecord(
  organizationId: string,
  record: OpenIssuesCacheRecord | null
) {
  if (!record) {
    openIssuesCache.delete(organizationId);
    return;
  }

  openIssuesCache.set(organizationId, record);
}

export function isOpenIssuesCacheValid(
  record: OpenIssuesCacheRecord | null | undefined
): boolean {
  return Boolean(record) && !isOpenIssuesCacheExpired(record ?? null);
}

export async function hydrateOpenIssuesCache(
  organizationId: string
): Promise<OpenIssuesCacheRecord | null> {
  if (!organizationId) {
    setCachedOpenIssuesRecord(organizationId, null);
    return null;
  }

  const record = await loadOpenIssuesCacheRecord(organizationId);
  setCachedOpenIssuesRecord(organizationId, record);
  return record;
}

/** קריאה סינכרונית מהמטמון - אחרי `hydrateOpenIssuesCache`. */
export function loadOpenIssuesCacheFromMemory(
  organizationId: string
): OpenIssuesCacheRecord | null {
  if (!organizationId) {
    return null;
  }

  return openIssuesCache.get(organizationId) ?? null;
}

export async function clearOpenIssuesOfflineCache(
  organizationId: string
): Promise<void> {
  setCachedOpenIssuesRecord(organizationId, null);
  await clearOpenIssuesCacheRecord(organizationId);
}

async function fetchOpenIssuesForProject(
  projectId: string
): Promise<QualityIssueOpenListResponse> {
  try {
    return await listProjectOpenQualityIssues(projectId);
  } catch {
    return {
      project_id: projectId,
      total: 0,
      items: [],
    };
  }
}

/**
 * מושך ליקויים פתוחים מה-API ושומר ב-IndexedDB.
 * נקרא בזמן «הכנה לא מקוון» - שגיאות per-project לא מפילות את כל המטמון.
 */
export async function refreshOpenIssuesCacheForOrganization(options: {
  organizationId: string;
  projectIds: string[];
  expiresAt: string;
}): Promise<OpenIssuesCacheRecord> {
  const uniqueProjectIds = [
    ...new Set(options.projectIds.map((projectId) => projectId.trim()).filter(Boolean)),
  ];

  const projects: OpenIssuesCacheRecord["projects"] = {};

  await Promise.all(
    uniqueProjectIds.map(async (projectId) => {
      const response = await fetchOpenIssuesForProject(projectId);
      projects[projectId] = {
        project_id: projectId,
        total: response.total,
        items: response.items,
      };
    })
  );

  const record: OpenIssuesCacheRecord = {
    organization_id: options.organizationId,
    cached_at: new Date().toISOString(),
    expires_at: options.expiresAt,
    projects,
  };

  const saved = await saveOpenIssuesCacheRecord(record);
  setCachedOpenIssuesRecord(options.organizationId, saved);
  return saved;
}

export async function getProjectOpenIssuesFromCache(
  organizationId: string,
  projectId: string
): Promise<QualityIssueOpenListResponse | null> {
  if (!organizationId || !projectId) {
    return null;
  }

  await hydrateOpenIssuesCache(organizationId);

  const fromMemory = loadOpenIssuesCacheFromMemory(organizationId);
  if (isOpenIssuesCacheValid(fromMemory)) {
    const snapshot = fromMemory?.projects[projectId];
    if (snapshot) {
      return {
        project_id: snapshot.project_id,
        total: snapshot.total,
        items: snapshot.items,
      };
    }
  }

  const snapshot = await getProjectOpenIssuesSnapshot(organizationId, projectId);
  if (!snapshot) {
    return null;
  }

  return {
    project_id: snapshot.project_id,
    total: snapshot.total,
    items: snapshot.items,
  };
}

const OPEN_ISSUE_CACHE_STATUSES: ReadonlySet<QualityIssueStatus> = new Set([
  "OPEN",
  "IN_REMEDIATION",
  "PENDING_VERIFICATION",
  "REOPENED",
]);

function shouldKeepIssueInOpenCache(issue: Pick<QualityIssue, "status">): boolean {
  return (
    OPEN_ISSUE_CACHE_STATUSES.has(issue.status) &&
    !isTerminalIssueStatus(issue.status)
  );
}

/** מעדכן מטמון offline אחרי שינוי סטטוס ליקוי משורת דוח (2.2.6). */
export async function patchOpenIssuesCacheAfterIssueUpdate(options: {
  organizationId: string;
  projectId: string;
  issue: QualityIssue;
}): Promise<void> {
  const { organizationId, projectId, issue } = options;
  if (!organizationId || !projectId) {
    return;
  }

  await hydrateOpenIssuesCache(organizationId);
  const record = loadOpenIssuesCacheFromMemory(organizationId);
  if (!record || isOpenIssuesCacheExpired(record)) {
    return;
  }

  const snapshot = record.projects[projectId];
  if (!snapshot) {
    return;
  }

  const withoutIssue = snapshot.items.filter((item) => item.id !== issue.id);
  const nextItems = shouldKeepIssueInOpenCache(issue)
    ? [...withoutIssue, issue]
    : withoutIssue;

  const nextRecord: OpenIssuesCacheRecord = {
    ...record,
    projects: {
      ...record.projects,
      [projectId]: {
        ...snapshot,
        total: nextItems.length,
        items: nextItems,
      },
    },
  };

  const saved = await saveOpenIssuesCacheRecord(nextRecord);
  setCachedOpenIssuesRecord(organizationId, saved);
}

export async function suggestProjectQualityIssueMatchesFromCache(
  organizationId: string,
  projectId: string,
  finding: FindingMatchInput,
  limit?: number
): Promise<QualityIssueSuggestMatchesResponse | null> {
  const openIssues = await getProjectOpenIssuesFromCache(
    organizationId,
    projectId
  );
  if (!openIssues) {
    return null;
  }

  const matchKey = matchKeyForFinding(finding);
  const candidates = findOpenIssueMatches(
    finding,
    openIssues.items,
    limit
  );

  return {
    project_id: projectId,
    match_key: matchKey,
    total: candidates.length,
    candidates,
  };
}
