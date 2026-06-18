import { apiFetch } from "@/lib/api/client";
import {
  importInProgressReportsFromOfflinePrep,
  type ImportInProgressReportsResult,
} from "@/lib/field-reports/import-in-progress-reports";
import {
  hydrateOfflinePrepBundle,
  isOfflinePrepValid,
  saveOfflinePrepBundle,
  type OfflinePrepBundle,
} from "@/lib/field-reports/offline-store";
import { refreshOpenIssuesCacheForOrganization } from "@/lib/quality-issues/open-issues-offline";

export type OfflinePrepFetchResult = {
  bundle: OfflinePrepBundle;
  importSummary: ImportInProgressReportsResult;
};

function extractProjectIds(bundle: OfflinePrepBundle): string[] {
  return (bundle.projects ?? [])
    .map((project) => project.id?.trim())
    .filter((projectId): projectId is string => Boolean(projectId));
}

export function offlinePrepIncludesProject(
  bundle: OfflinePrepBundle | null | undefined,
  projectId: string
): boolean {
  if (!bundle || !projectId.trim()) {
    return false;
  }

  const apartments = bundle.apartments_by_project?.[projectId];
  return Array.isArray(apartments);
}

export async function fetchAndPersistOfflinePrepBundle(options: {
  organizationId: string;
  userId?: string | null;
}): Promise<OfflinePrepFetchResult> {
  const { organizationId, userId } = options;

  const response = await apiFetch("/field-reports/offline-prep");

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      payload.error?.message
        || payload.message
        || payload.detail
        || "הכנה לא מקוון נכשלה"
    );
  }

  const payload = await response.json();
  const saved = await saveOfflinePrepBundle(organizationId, payload);
  const projectIds = extractProjectIds(saved);

  if (projectIds.length > 0 && saved.expires_at) {
    await refreshOpenIssuesCacheForOrganization({
      organizationId,
      projectIds,
      expiresAt: saved.expires_at,
    });
  }

  const importSummary = await importInProgressReportsFromOfflinePrep({
    organizationId,
    userId: userId ?? null,
    prepReports: payload.reports ?? [],
  });

  return {
    bundle: saved,
    importSummary,
  };
}

export async function ensureOfflinePrepForProject(options: {
  organizationId: string;
  projectId: string;
  userId?: string | null;
  force?: boolean;
}): Promise<OfflinePrepBundle | null> {
  const { organizationId, projectId, userId, force = false } = options;
  if (!organizationId || !projectId) {
    return null;
  }

  const existing = await hydrateOfflinePrepBundle(organizationId);
  if (
    !force
    && isOfflinePrepValid(existing)
    && offlinePrepIncludesProject(existing, projectId)
  ) {
    return existing;
  }

  const result = await fetchAndPersistOfflinePrepBundle({
    organizationId,
    userId,
  });
  return result.bundle;
}
