import { apiFetch } from "@/lib/api/client";
import {
  applyProjectPrefillToHeaderFields,
  type ProjectPrefillSource,
} from "@/lib/field-reports/project-header-prefill";
import {
  normalizeHeaderFields,
  patchHeaderFieldsBlocks,
  serializeHeaderFieldsForApi,
} from "@/lib/field-reports/header-fields";
import type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";
import {
  parseSupervisionCatalogFromBundle,
  parseSupervisionCatalogFromCatalogPayload,
} from "@/lib/field-reports/supervision-catalog";
import type {
  ConstructionStage,
  FieldReportDocumentType,
  PublicAreaId,
  SupervisionCatalog,
  SupervisionReportMeta,
  VisitScope,
} from "@/lib/field-reports/schema/types";
import { PUBLIC_AREA_DEFINITIONS } from "@/lib/field-reports/schema/types";
import { defaultInspectModeForDocumentType } from "@/lib/field-reports/quick-inspect";
import { buildSupervisionChecklist } from "@/lib/field-reports/supervision-checklist-builder";
import {
  saveLocalReport,
  type LocalVisitReportRecord,
} from "@/lib/field-reports/repositories/reports-repository";
import {
  syncNewVisitReportToServer,
  type SyncNewVisitReportToServerResult,
} from "@/lib/field-reports/new-report-form";

export type { SyncNewVisitReportToServerResult };

const VISIT_TYPE_LABELS: Record<string, string> = {
  STRUCTURE_SITE: "שלד / אתר",
  FINISHING_APARTMENTS: "גמר דירות",
  MIXED: "סיור משולב",
};

/** מיפוי שלב בנייה → visit_type (§10.3). */
export function deriveVisitTypeFromConstructionStage(
  constructionStage: ConstructionStage
): string {
  switch (constructionStage) {
    case "STRUCTURE":
      return "STRUCTURE_SITE";
    case "FINISHING":
      return "FINISHING_APARTMENTS";
    case "MIXED":
      return "MIXED";
    default:
      return "MIXED";
  }
}

export function visitTypeLabelHe(visitType: string): string {
  return VISIT_TYPE_LABELS[visitType] ?? visitType;
}

export async function fetchSupervisionCatalogFromApi(): Promise<SupervisionCatalog> {
  const response = await apiFetch("/field-reports/catalog?visit_type=MIXED");

  if (!response.ok) {
    throw new Error("טעינת קטלוג supervision נכשלה");
  }

  const payload = (await response.json()) as Record<string, unknown>;
  const catalog = parseSupervisionCatalogFromCatalogPayload(payload);

  if (!catalog?.issues.length) {
    throw new Error("קטלוג supervision אינו זמין");
  }

  return catalog;
}

export function loadSupervisionCatalogFromOfflineBundle(
  bundle: OfflinePrepBundle
): SupervisionCatalog {
  const catalog = parseSupervisionCatalogFromBundle(bundle);

  if (!catalog?.issues.length) {
    throw new Error(
      "חבילת ההכנה אינה כוללת קטלוג supervision. בצע הכנה לא מקוון מחדש."
    );
  }

  return catalog;
}

export type CreateSupervisionLocalReportParams = {
  organizationId: string;
  userId?: string | null;
  projectId: string;
  projectName?: string | null;
  visitDate: string;
  catalog: SupervisionCatalog;
  constructionStage: ConstructionStage;
  visitScope: VisitScope;
  documentType?: FieldReportDocumentType;
  apartmentId?: string | null;
  apartmentNumber?: string | null;
  ownerName?: string | null;
  adHocApartment?: boolean;
  publicAreaId?: PublicAreaId;
  catalogVersion?: string | null;
  organizationProfileSnapshot?: unknown;
  projectPrefill?: ProjectPrefillSource | null;
};

function buildSupervisionMeta(
  params: CreateSupervisionLocalReportParams
): SupervisionReportMeta {
  const publicArea = PUBLIC_AREA_DEFINITIONS.find(
    (area) => area.id === params.publicAreaId
  );

  const documentType = params.documentType ?? "weekly_inspection";

  return {
    document_type: documentType,
    inspect_mode: defaultInspectModeForDocumentType(documentType),
    construction_stage: params.constructionStage,
    visit_scope: params.visitScope,
    apartment_id: params.apartmentId ?? null,
    apartment_number: params.apartmentNumber ?? null,
    owner_name: params.ownerName ?? null,
    ad_hoc_apartment: params.adHocApartment ?? false,
    public_area_id: params.publicAreaId ?? null,
    public_area_label_he: publicArea?.label_he ?? null,
  };
}

/** יוצר דוח מקומי עם בלוק supervision_checklist (§11.4, §13.3). */
export async function createSupervisionLocalReport(
  params: CreateSupervisionLocalReportParams
): Promise<LocalVisitReportRecord> {
  const visitType = deriveVisitTypeFromConstructionStage(
    params.constructionStage
  );
  const supervisionMeta = buildSupervisionMeta(params);

  const checklistBlock = buildSupervisionChecklist({
    catalog: params.catalog,
    constructionStage: params.constructionStage,
    visitScope: params.visitScope,
    publicAreaId: params.publicAreaId,
    apartmentId: params.apartmentId,
    apartmentNumber: params.apartmentNumber,
    adHocApartment: params.adHocApartment,
  });

  if (!checklistBlock.items.length) {
    throw new Error("לא נמצאו פריטי צ'קליסט לבחירה");
  }

  let normalized = normalizeHeaderFields({}, visitType, {
    visitDate: params.visitDate,
  });

  if (params.projectPrefill) {
    normalized = applyProjectPrefillToHeaderFields(
      normalized,
      params.projectPrefill
    );
  }

  normalized = patchHeaderFieldsBlocks(
    normalized,
    [checklistBlock],
    visitType
  );

  const headerFields = serializeHeaderFieldsForApi(normalized);
  headerFields.supervision_meta = supervisionMeta;

  return saveLocalReport({
    organization_id: params.organizationId,
    user_id: params.userId ?? null,
    project_id: params.projectId,
    project_name: params.projectName ?? null,
    visit_type: visitType,
    visit_type_label_he: visitTypeLabelHe(visitType),
    visit_date: params.visitDate,
    header_fields: headerFields,
    local_status: "LOCAL_IN_PROGRESS",
    catalog_version: params.catalogVersion ?? params.catalog.catalog_version ?? null,
    organization_profile_snapshot:
      (params.organizationProfileSnapshot as Record<string, unknown> | null
        | undefined) ?? null,
  });
}

export { syncNewVisitReportToServer };
