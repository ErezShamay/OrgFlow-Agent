import { getQualityIssueDetail } from "@/lib/quality-issues/api";
import { getProjectOpenIssuesFromCache } from "@/lib/quality-issues/open-issues-offline";
import type { QualityIssue } from "@/lib/quality-issues/types";

export async function resolveLinkedIssueForFindingLine(options: {
  projectId: string;
  organizationId?: string | null;
  linkedIssueId: string;
  isOnline: boolean;
}): Promise<QualityIssue | null> {
  const { projectId, organizationId, linkedIssueId, isOnline } = options;

  if (organizationId) {
    const cached = await getProjectOpenIssuesFromCache(
      organizationId,
      projectId
    );
    const fromCache = cached?.items.find((issue) => issue.id === linkedIssueId);
    if (fromCache) {
      return fromCache;
    }
  }

  if (!isOnline) {
    return null;
  }

  try {
    const detail = await getQualityIssueDetail(linkedIssueId);
    return detail.issue;
  } catch {
    return null;
  }
}
