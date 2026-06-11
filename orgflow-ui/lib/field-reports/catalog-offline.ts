import {
  hydrateOfflinePrepBundle,
  loadOfflinePrepBundle,
  type OfflinePrepBundle,
} from "@/lib/field-reports/offline-store";
import {
  getCatalogForVisitType,
} from "@/lib/field-reports/repositories/catalog-repository";

export type CatalogPayload = {
  catalog_version?: string | null;
  families?: Array<{
    top_family: string;
    label_he?: string;
    issue_count?: number;
  }>;
  categories?: Array<{
    top_family: string;
    category_id: string;
    category_name_he: string;
  }>;
  issues?: Array<{
    issue_id: string;
    issue_name_he: string;
    standard_ref?: string | null;
    top_family: string;
    category_id: string;
    category_name_he: string;
    severity?: string | null;
    description?: string | null;
  }>;
};

export const OFFLINE_CATALOG_UNAVAILABLE_MESSAGE =
  "אין מפרט מקומי - בצע «הכנה לא מקוון» כשיש רשת.";

export async function loadOfflineCatalogForVisitType(
  organizationId: string,
  visitType: string
): Promise<CatalogPayload | null> {
  return getCatalogForVisitType(organizationId, visitType);
}

/**
 * טוען קטלוג מ-IndexedDB (עם hydrate) ל-picker - בלי קריאת API (FR-014).
 */
export async function loadOfflineCatalogForPicker(
  organizationId: string,
  visitType: string
): Promise<CatalogPayload | null> {
  if (!organizationId || !visitType) {
    return null;
  }

  await hydrateOfflinePrepBundle(organizationId);

  const fromIndexedDb = await loadOfflineCatalogForVisitType(
    organizationId,
    visitType
  );
  if (fromIndexedDb?.issues?.length) {
    return fromIndexedDb;
  }

  const fromCache = loadOfflineCatalogForVisitTypeFromCache(
    organizationId,
    visitType
  );
  if (fromCache?.issues?.length) {
    return fromCache;
  }

  return null;
}

export function catalogPayloadHasIssues(
  payload: CatalogPayload | null | undefined
): payload is CatalogPayload {
  return Boolean(payload?.issues?.length);
}

/** גרסה סינכרונית - רק אם המטמון כבר הותהלם (`hydrateOfflinePrepBundle`). */
export function loadOfflineCatalogForVisitTypeFromCache(
  organizationId: string,
  visitType: string
): CatalogPayload | null {
  const bundle = loadOfflinePrepBundle(organizationId);
  if (!bundle) {
    return null;
  }

  return filterCatalogForVisitType(bundle, visitType);
}

/** מסנן קטלוג לפי משפחות מותרות לסוג ביקור - משותף ל-localStorage ול-IndexedDB. */
export function filterCatalogForVisitType(
  bundle: OfflinePrepBundle,
  visitType: string
): CatalogPayload | null {
  if (!bundle?.catalog) {
    return null;
  }

  const fullCatalog = bundle.catalog as CatalogPayload;
  const allowedFamilies = visitTypeAllowedFamilies(bundle, visitType);

  if (!allowedFamilies.length) {
    return fullCatalog;
  }

  const allowed = new Set(allowedFamilies);
  return {
    catalog_version: fullCatalog.catalog_version,
    families: (fullCatalog.families || []).filter((family) =>
      allowed.has(family.top_family)
    ),
    categories: (fullCatalog.categories || []).filter((category) =>
      allowed.has(category.top_family)
    ),
    issues: (fullCatalog.issues || []).filter((issue) =>
      allowed.has(issue.top_family)
    ),
  };
}

function visitTypeAllowedFamilies(
  bundle: OfflinePrepBundle,
  visitType: string
): string[] {
  const visitTypes = bundle.visit_types as Array<{
    code?: string;
    allowed_top_families?: string[];
  }>;

  const match = visitTypes.find((entry) => entry.code === visitType);
  return match?.allowed_top_families || [];
}
