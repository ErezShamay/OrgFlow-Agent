import type {
  ConstructionStage,
  PublicAreaId,
  SupervisionCatalog,
  SupervisionCatalogIssue,
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
  VisitScope,
} from "@/lib/field-reports/schema/types";
import { PUBLIC_AREA_DEFINITIONS } from "@/lib/field-reports/schema/types";

export type BuildSupervisionChecklistParams = {
  catalog: SupervisionCatalog;
  constructionStage: ConstructionStage;
  visitScope: VisitScope;
  publicAreaId?: PublicAreaId;
  blockId?: string;
  titleHe?: string;
  apartmentId?: string | null;
  apartmentNumber?: string | null;
  adHocApartment?: boolean;
  sortOrder?: number;
};

/** מסנן פריטי קטלוג לפי שלב, היקף ואזור ציבורי (§6.2, §11). */
export function filterSupervisionCatalogIssues(params: {
  catalog: SupervisionCatalog;
  constructionStage: ConstructionStage;
  visitScope: VisitScope;
  publicAreaId?: PublicAreaId;
}): SupervisionCatalogIssue[] {
  const { catalog, constructionStage, visitScope, publicAreaId } = params;

  return (catalog.issues ?? []).filter((issue) =>
    matchesSupervisionCatalogIssue({
      issue,
      constructionStage,
      visitScope,
      publicAreaId,
    })
  );
}

export function matchesSupervisionCatalogIssue(params: {
  issue: SupervisionCatalogIssue;
  constructionStage: ConstructionStage;
  visitScope: VisitScope;
  publicAreaId?: PublicAreaId;
}): boolean {
  const { issue, constructionStage, visitScope, publicAreaId } = params;

  if (!matchesConstructionStage(issue, constructionStage)) {
    return false;
  }

  if (visitScope === "APARTMENT" || visitScope === "MULTI_APARTMENT") {
    return issue.scope === "APARTMENT" || issue.scope === "BOTH";
  }

  if (visitScope === "WHOLE_BUILDING") {
    return true;
  }

  if (issue.scope !== "PUBLIC_AREA" && issue.scope !== "BOTH") {
    return false;
  }

  if (!issue.public_area_id) {
    return true;
  }

  return Boolean(publicAreaId && issue.public_area_id === publicAreaId);
}

function matchesConstructionStage(
  issue: SupervisionCatalogIssue,
  constructionStage: ConstructionStage
): boolean {
  if (constructionStage === "MIXED") {
    return true;
  }

  return issue.allowed_stages.includes(constructionStage);
}

function catalogIssueToChecklistItem(
  issue: SupervisionCatalogIssue,
  sortOrder: number
): SupervisionChecklistItem {
  return {
    id: `checklist-${issue.issue_id}`,
    catalog_issue_id: issue.issue_id,
    issue_name_he: issue.issue_name_he,
    category_id: issue.category_id,
    category_name_he: issue.category_name_he,
    top_family: issue.top_family,
    standard_ref: issue.standard_ref,
    severity: issue.severity ?? null,
    status: "UNCHECKED",
    notes: null,
    photo_ids: [],
    linked_line_id: null,
    sort_order: sortOrder,
  };
}

export function defaultSupervisionChecklistTitleHe(params: {
  visitScope: VisitScope;
  apartmentNumber?: string | null;
  publicAreaId?: PublicAreaId;
}): string {
  if (params.visitScope === "APARTMENT" || params.visitScope === "MULTI_APARTMENT") {
    const number = params.apartmentNumber?.trim();
    return number ? `ביקור דירה ${number}` : "ביקור דירה";
  }

  if (params.visitScope === "WHOLE_BUILDING") {
    return "ביקור כלל הבניין";
  }

  const area = PUBLIC_AREA_DEFINITIONS.find(
    (entry) => entry.id === params.publicAreaId
  );
  return area ? `ביקור ${area.label_he}` : "ביקור שטחים ציבוריים";
}

/** בונה בלוק supervision_checklist מקטלוג מסונן (§11.4). */
export function buildSupervisionChecklist(
  params: BuildSupervisionChecklistParams
): SupervisionChecklistBlock {
  const filtered = filterSupervisionCatalogIssues({
    catalog: params.catalog,
    constructionStage: params.constructionStage,
    visitScope: params.visitScope,
    publicAreaId: params.publicAreaId,
  });

  const items = filtered.map((issue, index) =>
    catalogIssueToChecklistItem(issue, index)
  );

  return {
    id: params.blockId ?? "checklist-main",
    kind: "supervision_checklist",
    title_he:
      params.titleHe ??
      defaultSupervisionChecklistTitleHe({
        visitScope: params.visitScope,
        apartmentNumber: params.apartmentNumber,
        publicAreaId: params.publicAreaId,
      }),
    sort_order: params.sortOrder ?? 0,
    construction_stage: params.constructionStage,
    visit_scope: params.visitScope,
    apartment_id: params.apartmentId ?? null,
    apartment_number: params.apartmentNumber ?? null,
    ad_hoc_apartment: params.adHocApartment ?? false,
    public_area_id: params.publicAreaId ?? null,
    items,
  };
}

/** מזהה דוח עם בלוק supervision_checklist (§15.2). */
export function isSupervisionChecklistReport(
  blocks: Array<{ kind?: string }> | null | undefined
): boolean {
  return (
    blocks?.some((block) => block.kind === "supervision_checklist") ?? false
  );
}
