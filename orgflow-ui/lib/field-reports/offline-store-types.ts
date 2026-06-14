import type { ProjectApartment } from "@/lib/apartments/types";
import type {
  PublicAreaDefinition,
  SupervisionCatalog,
} from "@/lib/field-reports/schema/types";

export type OfflinePrepBundle = {
  organization_id: string;
  offline_max_days: number;
  prepared_at: string;
  expires_at: string;
  catalog_version?: string | null;
  catalog: unknown;
  /** קטלוג supervision מסונן (§12.1). */
  supervision_catalog?: SupervisionCatalog | null;
  /** אזורים ציבוריים — נספח א' (§12.1). */
  public_areas?: PublicAreaDefinition[] | null;
  /** דירות לפי project_id (§12.1). */
  apartments_by_project?: Record<string, ProjectApartment[]> | null;
  visit_types: unknown[];
  organization_profile: unknown;
  projects: unknown[];
  reports: unknown[];
};
