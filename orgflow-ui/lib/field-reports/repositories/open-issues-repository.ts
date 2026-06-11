import {
  FIELD_REPORT_STORES,
  type OpenIssuesCacheRecord,
  type ProjectOpenIssuesSnapshot,
} from "@/lib/field-reports/db/schema";
import { getFieldReportDatabase } from "@/lib/field-reports/db/field-report-db";

export type { OpenIssuesCacheRecord, ProjectOpenIssuesSnapshot };

export function isOpenIssuesCacheExpired(
  record: OpenIssuesCacheRecord | null
): boolean {
  if (!record?.expires_at) {
    return true;
  }

  return new Date(record.expires_at).getTime() <= Date.now();
}

export async function loadOpenIssuesCacheRecord(
  organizationId: string
): Promise<OpenIssuesCacheRecord | null> {
  if (!organizationId) {
    return null;
  }

  const database = await getFieldReportDatabase();
  const record = await database.get(
    FIELD_REPORT_STORES.open_issues,
    organizationId
  );
  return record ?? null;
}

export async function saveOpenIssuesCacheRecord(
  record: OpenIssuesCacheRecord
): Promise<OpenIssuesCacheRecord> {
  const database = await getFieldReportDatabase();
  await database.put(FIELD_REPORT_STORES.open_issues, record);
  return record;
}

export async function clearOpenIssuesCacheRecord(
  organizationId: string
): Promise<void> {
  if (!organizationId) {
    return;
  }

  const database = await getFieldReportDatabase();
  await database.delete(FIELD_REPORT_STORES.open_issues, organizationId);
}

export async function getProjectOpenIssuesSnapshot(
  organizationId: string,
  projectId: string
): Promise<ProjectOpenIssuesSnapshot | null> {
  const record = await loadOpenIssuesCacheRecord(organizationId);
  if (!record || isOpenIssuesCacheExpired(record)) {
    return null;
  }

  return record.projects[projectId] ?? null;
}
