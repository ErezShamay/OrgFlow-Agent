/**
 * Resolves suggest-matches from API when online, with IndexedDB fallback (2.1.8).
 */

import { suggestProjectQualityIssueMatches } from "@/lib/quality-issues/api";
import { suggestProjectQualityIssueMatchesFromCache } from "@/lib/quality-issues/open-issues-offline";
import type {
  QualityIssueSuggestMatchesRequest,
  QualityIssueSuggestMatchesResponse,
} from "@/lib/quality-issues/types";

export type ResolveSuggestMatchesOptions = {
  projectId: string;
  organizationId?: string | null;
  request: QualityIssueSuggestMatchesRequest;
  isOnline?: boolean;
};

export async function resolveProjectQualityIssueMatches(
  options: ResolveSuggestMatchesOptions
): Promise<QualityIssueSuggestMatchesResponse> {
  const { projectId, organizationId, request, isOnline = true } = options;

  if (isOnline) {
    try {
      return await suggestProjectQualityIssueMatches(projectId, request);
    } catch {
      // fall through to offline cache
    }
  }

  if (organizationId) {
    const cached = await suggestProjectQualityIssueMatchesFromCache(
      organizationId,
      projectId,
      request,
      request.limit
    );
    if (cached) {
      return cached;
    }
  }

  if (isOnline) {
    return suggestProjectQualityIssueMatches(projectId, request);
  }

  throw new Error("לא ניתן לטעון ליקויים דומים");
}
