import { apiFetch } from "@/lib/api/client";
import { readApiErrorMessage } from "@/lib/api/read-error-message";
import {
  applySupervisionDefectLinesToReport,
  supervisionVisitGroupKey,
  supervisionVisitLocation,
} from "@/lib/field-reports/checklist-defect-to-line";
import { normalizeHeaderFields } from "@/lib/field-reports/header-fields";
import { normalizeSupervisionMeta } from "@/lib/field-reports/schema/normalize";
import type {
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
} from "@/lib/field-reports/schema/types";
import type { LocalVisitReportRecord } from "@/lib/field-reports/repositories/reports-repository";
import { patchOpenIssuesCacheAfterIssueUpdate } from "@/lib/quality-issues/open-issues-offline";
import {
  buildMaterializationKey,
  parseQualityIssue,
  type QualityIssue,
} from "@/lib/quality-issues/types";

export type DraftMaterializationResponse = {
  draft_materialization: {
    report_id: string;
    line_id: string;
    project_id: string;
    issue_id: string;
    created: boolean;
    visibility: string;
  };
  issue: QualityIssue;
};

function buildLocalDraftIssue(params: {
  organizationId: string;
  projectId: string;
  reportId: string;
  lineId: string;
  item: SupervisionChecklistItem;
  block: SupervisionChecklistBlock;
  seenAt: string;
}): QualityIssue {
  const { organizationId, projectId, reportId, lineId, item, block, seenAt } =
    params;
  const meta = {
    construction_stage: block.construction_stage,
    visit_scope: block.visit_scope,
    apartment_number: block.apartment_number,
    public_area_id: block.public_area_id,
    public_area_label_he: null,
  };
  const location = supervisionVisitLocation(meta);
  const groupKey = supervisionVisitGroupKey(meta);

  return parseQualityIssue({
    id: `draft-local-${lineId}`,
    organization_id: organizationId,
    project_id: projectId,
    title: item.issue_name_he,
    description: item.notes ?? null,
    location,
    trade: item.category_name_he,
    group_key: groupKey,
    group_label_he: location,
    standard_ref: item.standard_ref,
    severity: item.severity ?? "MEDIUM",
    status: "OPEN",
    visibility: "DRAFT",
    catalog_issue_id: item.catalog_issue_id,
    first_seen_report_id: reportId,
    first_seen_line_id: lineId,
    first_seen_at: seenAt,
    last_seen_report_id: reportId,
    last_seen_line_id: lineId,
    last_seen_at: seenAt,
    photo_ids: item.photo_ids,
    materialization_key: buildMaterializationKey(reportId, lineId),
    recurrence_count: 0,
    created_at: seenAt,
    updated_at: seenAt,
  });
}

export async function requestDefectDraftMaterialization(params: {
  serverReportId: string;
  serverLineId: string;
  checklistItemId: string;
}): Promise<DraftMaterializationResponse | null> {
  const response = await apiFetch(
    `/field-reports/visits/${encodeURIComponent(params.serverReportId)}/lines/${encodeURIComponent(params.serverLineId)}/draft-issue`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        checklist_item_id: params.checklistItemId,
      }),
    }
  );

  if (!response.ok) {
    const message = await readApiErrorMessage(response);
    throw new Error(message || "יצירת ליקוי טיוטה נכשלה");
  }

  const payload = (await response.json()) as {
    draft_materialization: DraftMaterializationResponse["draft_materialization"];
    issue: unknown;
  };

  return {
    draft_materialization: payload.draft_materialization,
    issue: parseQualityIssue(payload.issue),
  };
}

async function persistDraftIssueLocally(params: {
  organizationId: string;
  projectId: string;
  issue: QualityIssue;
}): Promise<void> {
  await patchOpenIssuesCacheAfterIssueUpdate({
    organizationId: params.organizationId,
    projectId: params.projectId,
    issue: params.issue,
  });
}

/**
 * L1 — DEFECT → שורת ממצא + DRAFT issue (API when synced, else open_issues cache).
 */
export async function syncSupervisionDefectDraftsForReport(
  record: LocalVisitReportRecord
): Promise<LocalVisitReportRecord> {
  const synced = applySupervisionDefectLinesToReport(record);
  const normalized = normalizeHeaderFields(
    synced.header_fields,
    synced.visit_type
  );
  const block = normalized.blocks.find(
    (entry): entry is SupervisionChecklistBlock =>
      entry.kind === "supervision_checklist"
  );
  const meta = normalizeSupervisionMeta(synced.header_fields);

  if (!block || !meta) {
    return synced;
  }

  const serverReportId = synced.server_report_id?.trim();
  const seenAt = new Date().toISOString();

  for (const item of block.items) {
    if (item.status !== "DEFECT" || !item.linked_line_id) {
      continue;
    }

    const localLine = synced.lines.find(
      (line) =>
        line.client_line_uuid === item.linked_line_id ||
        line.id === item.linked_line_id
    );
    const serverLineId = localLine?.server_line_id?.trim() ?? null;

    if (serverReportId && serverLineId) {
      try {
        const result = await requestDefectDraftMaterialization({
          serverReportId,
          serverLineId,
          checklistItemId: item.id,
        });
        if (result?.issue) {
          await persistDraftIssueLocally({
            organizationId: synced.organization_id,
            projectId: synced.project_id,
            issue: result.issue,
          });
        }
        continue;
      } catch {
        // Fall through to local draft cache when API is unavailable.
      }
    }

    const reportKey = serverReportId ?? synced.client_report_uuid;
    const lineKey = serverLineId ?? item.linked_line_id;
    const localIssue = buildLocalDraftIssue({
      organizationId: synced.organization_id,
      projectId: synced.project_id,
      reportId: reportKey,
      lineId: lineKey,
      item,
      block,
      seenAt,
    });
    await persistDraftIssueLocally({
      organizationId: synced.organization_id,
      projectId: synced.project_id,
      issue: localIssue,
    });
  }

  return synced;
}
