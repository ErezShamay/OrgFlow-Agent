import type { CatalogPayload } from "@/lib/field-reports/catalog-offline";
import type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";
import type {
  CatalogIssueScope,
  ConstructionStage,
  PublicAreaId,
  SupervisionCatalog,
  SupervisionCatalogIssue,
} from "@/lib/field-reports/schema/types";
import {
  CATALOG_ISSUE_SCOPES,
  CONSTRUCTION_STAGES,
  PUBLIC_AREA_DEFINITIONS,
} from "@/lib/field-reports/schema/types";

const PUBLIC_AREA_IDS = new Set<string>(
  PUBLIC_AREA_DEFINITIONS.map((area) => area.id)
);

function isCatalogIssueScope(value: string): value is CatalogIssueScope {
  return (CATALOG_ISSUE_SCOPES as readonly string[]).includes(value);
}

function isConstructionStage(value: string): value is ConstructionStage {
  return (CONSTRUCTION_STAGES as readonly string[]).includes(value);
}

function normalizePublicAreaId(value: unknown): PublicAreaId | null {
  if (typeof value !== "string" || !PUBLIC_AREA_IDS.has(value)) {
    return null;
  }

  return value as PublicAreaId;
}

function normalizeSupervisionCatalogIssue(
  raw: Record<string, unknown>
): SupervisionCatalogIssue | null {
  const issueId = String(raw.issue_id ?? "").trim();
  const issueNameHe = String(raw.issue_name_he ?? "").trim();
  const standardRef = String(raw.standard_ref ?? "").trim();
  const topFamily = String(raw.top_family ?? "").trim();
  const categoryId = String(raw.category_id ?? "").trim();
  const categoryNameHe = String(raw.category_name_he ?? "").trim();
  const scope = String(raw.scope ?? "").trim();

  if (
    !issueId ||
    !issueNameHe ||
    !standardRef ||
    !topFamily ||
    !categoryId ||
    !categoryNameHe ||
    !isCatalogIssueScope(scope)
  ) {
    return null;
  }

  const allowedStages = Array.isArray(raw.allowed_stages)
    ? raw.allowed_stages
        .map((stage) => String(stage ?? "").trim())
        .filter(isConstructionStage)
    : [];

  if (!allowedStages.length) {
    return null;
  }

  return {
    issue_id: issueId,
    issue_name_he: issueNameHe,
    standard_ref: standardRef,
    catalog_reference_id:
      typeof raw.catalog_reference_id === "string"
        ? raw.catalog_reference_id
        : null,
    top_family: topFamily,
    category_id: categoryId,
    category_name_he: categoryNameHe,
    severity: typeof raw.severity === "string" ? raw.severity : null,
    description: typeof raw.description === "string" ? raw.description : null,
    scope,
    public_area_id: normalizePublicAreaId(raw.public_area_id),
    allowed_stages: allowedStages,
  };
}

/** מחלץ קטלוג supervision מ-payload קטלוג מלא (offline prep / API). */
export function parseSupervisionCatalogFromCatalogPayload(
  payload: CatalogPayload | Record<string, unknown> | null | undefined
): SupervisionCatalog | null {
  const issuesRaw = (payload as CatalogPayload | null | undefined)?.issues;
  if (!Array.isArray(issuesRaw)) {
    return null;
  }

  const issues = issuesRaw
    .map((issue) =>
      issue && typeof issue === "object"
        ? normalizeSupervisionCatalogIssue(issue as Record<string, unknown>)
        : null
    )
    .filter((issue): issue is SupervisionCatalogIssue => issue !== null);

  if (!issues.length) {
    return null;
  }

  const catalogVersion =
    typeof (payload as CatalogPayload | null)?.catalog_version === "string"
      ? (payload as CatalogPayload).catalog_version
      : null;

  return {
    catalog_version: catalogVersion,
    issues,
  };
}

export function parseSupervisionCatalogFromBundle(
  bundle: OfflinePrepBundle
): SupervisionCatalog | null {
  const dedicated = parseSupervisionCatalogFromCatalogPayload(
    bundle.supervision_catalog as CatalogPayload | Record<string, unknown> | null
  );
  if (dedicated?.issues.length) {
    return dedicated;
  }

  return parseSupervisionCatalogFromCatalogPayload(
    bundle.catalog as CatalogPayload
  );
}
