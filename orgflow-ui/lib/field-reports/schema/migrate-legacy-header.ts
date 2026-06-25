import type { ProjectMetadata, Stakeholder, StakeholderRole } from "./types";
import { normalizeOptionalTextInput } from "@/lib/validation/optional-field-display";

/** מיפוי שדות legacy ב-header_fields לתפקיד stakeholder. */
const LEGACY_STAKEHOLDER_FIELDS: ReadonlyArray<{
  field: string;
  role: StakeholderRole;
}> = [
  { field: "developer_name", role: "developer" },
  { field: "developer_pm_name", role: "project_manager" },
  { field: "contractor_name", role: "contractor" },
  { field: "lawyer_name", role: "lawyer_tenants" },
  { field: "accompanying_lawyer", role: "lawyer_accompanying" },
];

/**
 * ממיר שדות legacy (developer_name וכו') לרשימת stakeholders.
 * שדות ריקים מדולגים.
 */
export function migrateLegacyStakeholdersFromHeader(
  headerFields: Record<string, unknown>
): Stakeholder[] {
  const stakeholders: Stakeholder[] = [];

  for (const { field, role } of LEGACY_STAKEHOLDER_FIELDS) {
    const name = stringField(headerFields[field]);
    if (!name) {
      continue;
    }
    stakeholders.push({
      id: `legacy-${role}`,
      role,
      name,
    });
  }

  const architectName = stringField(headerFields.architect_name);
  if (architectName) {
    stakeholders.push({
      id: "legacy-architect",
      role: "architect",
      name: architectName,
    });
  }

  return stakeholders;
}

/**
 * מחלץ ProjectMetadata משדות legacy ב-header_fields (לפני FR-1.1).
 */
export function migrateLegacyProjectMetadataFromHeader(
  headerFields: Record<string, unknown>
): Partial<ProjectMetadata> {
  const metadata: Partial<ProjectMetadata> = {};

  const siteAddress = stringField(headerFields.site_address);
  if (siteAddress) {
    metadata.site_address = siteAddress;
  }

  const architectName = stringField(headerFields.architect_name);
  if (architectName) {
    metadata.architect_name = architectName;
  }

  assignOptionalString(metadata, "scheme", headerFields.scheme);
  assignOptionalString(metadata, "scheme_label_he", headerFields.scheme_label_he);
  assignOptionalString(
    metadata,
    "project_start_date",
    headerFields.project_start_date
  );
  assignOptionalString(
    metadata,
    "project_end_date",
    headerFields.project_end_date
  );
  assignOptionalString(
    metadata,
    "project_grace_end_date",
    headerFields.project_grace_end_date
  );
  assignOptionalString(
    metadata,
    "structure_documentation_date",
    headerFields.structure_documentation_date
  );
  assignOptionalString(
    metadata,
    "addressee_label_he",
    headerFields.addressee_label_he
  );
  assignOptionalString(metadata, "gantt_forecast", headerFields.gantt_forecast);
  assignOptionalString(
    metadata,
    "illustration_caption_he",
    headerFields.illustration_caption_he
  );
  assignOptionalString(
    metadata,
    "tenant_changes_notes",
    headerFields.tenant_changes_notes
  );

  const housingUnits = headerFields.housing_units_count;
  if (typeof housingUnits === "number" && Number.isFinite(housingUnits)) {
    metadata.housing_units_count = housingUnits;
  }

  return metadata;
}

function assignOptionalString(
  target: Partial<ProjectMetadata>,
  key: keyof ProjectMetadata,
  value: unknown
): void {
  const text = stringField(value);
  if (text) {
    (target as Record<string, string>)[key] = text;
  }
}

function stringField(value: unknown): string {
  if (typeof value === "string") {
    return normalizeOptionalTextInput(value);
  }
  if (value === null || value === undefined) {
    return "";
  }
  return normalizeOptionalTextInput(String(value));
}
