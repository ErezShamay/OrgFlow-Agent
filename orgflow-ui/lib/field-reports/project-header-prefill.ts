import type { ReportHeaderFields } from "./header-fields";
import { projectSchemeLabelHe } from "./project-scheme-labels";
import {
  mergeStakeholderPrefill,
  stakeholdersFromProject,
  type ProjectStakeholderSource,
} from "./project-stakeholder-prefill";
import type { ProjectMetadata, ProjectScheme } from "./schema/types";

/** מקור prefill מישות פרויקט - mirrors backend field_report_project_prefill (FR-4.3). */
export type ProjectPrefillSource = ProjectStakeholderSource & {
  city?: string | null;
  scheme?: string | null;
  housing_units_count?: number | null;
  project_start_date?: string | null;
  project_end_date?: string | null;
  project_grace_end_date?: string | null;
  structure_documentation_date?: string | null;
  illustration_url?: string | null;
  illustration_source_he?: string | null;
};

const VALID_SCHEMES = new Set<ProjectScheme>([
  "TAMA38_STRENGTHENING",
  "TAMA38_DEMOLITION_REBUILD",
  "TAMA38_RELOCATED_BUILD",
]);

function pickText(...values: Array<string | null | undefined>): string {
  for (const value of values) {
    const text = value?.trim();
    if (text) {
      return text;
    }
  }
  return "";
}

function isValidScheme(value: string | null | undefined): value is ProjectScheme {
  return Boolean(value && VALID_SCHEMES.has(value as ProjectScheme));
}

/** בונה metadata לכותרת דוח - רק שדות זמינים בפרויקט. */
export function projectMetadataFromProject(
  project: ProjectPrefillSource
): Partial<ProjectMetadata> {
  const metadata: Partial<ProjectMetadata> = {};

  if (isValidScheme(project.scheme)) {
    metadata.scheme = project.scheme;
    metadata.scheme_label_he = projectSchemeLabelHe(project.scheme);
  }

  const siteAddress = pickText(project.city);
  if (siteAddress) {
    metadata.site_address = siteAddress;
  }

  const architectName = pickText(project.architect_name);
  if (architectName) {
    metadata.architect_name = architectName;
  }

  for (const key of [
    "project_start_date",
    "project_end_date",
    "project_grace_end_date",
    "structure_documentation_date",
  ] as const) {
    const value = pickText(project[key]);
    if (value) {
      metadata[key] = value;
    }
  }

  if (
    typeof project.housing_units_count === "number"
    && Number.isFinite(project.housing_units_count)
  ) {
    metadata.housing_units_count = project.housing_units_count;
  }

  const illustrationUrl = pickText(project.illustration_url);
  if (illustrationUrl) {
    metadata.illustration_url = illustrationUrl;
  }

  const illustrationSource = pickText(project.illustration_source_he);
  if (illustrationSource) {
    metadata.illustration_source_he = illustrationSource;
  }

  return metadata;
}

function mergeMetadataPrefill(
  existing: ProjectMetadata,
  prefill: Partial<ProjectMetadata>
): ProjectMetadata {
  const merged: ProjectMetadata = { ...existing };

  for (const [key, value] of Object.entries(prefill) as Array<
    [keyof ProjectMetadata, ProjectMetadata[keyof ProjectMetadata]]
  >) {
    const current = merged[key];
    if (current !== null && current !== undefined && current !== "") {
      continue;
    }
    if (value === null || value === undefined || value === "") {
      continue;
    }
    (merged as Record<string, unknown>)[key] = value;
  }

  return merged;
}

/**
 * ממלא שדות כותרת ריקים מפרויקט - לא דורס ערכים שכבר הוזנו בדוח.
 * השדות נשארים ניתנים לעריכה ב-UI.
 */
export function applyProjectPrefillToHeaderFields(
  header: ReportHeaderFields,
  project: ProjectPrefillSource
): ReportHeaderFields {
  const prefillMetadata = projectMetadataFromProject(project);
  const project_metadata = mergeMetadataPrefill(
    header.project_metadata,
    prefillMetadata
  );

  const site_address =
    pickText(header.site_address, project_metadata.site_address, project.city)
    || header.site_address;

  const developer_name =
    pickText(header.developer_name, project.developer_name)
    || header.developer_name;

  const developer_pm_name =
    pickText(
      header.developer_pm_name,
      project.developer_pm_name,
      project.contractor_name
    ) || header.developer_pm_name;

  const contractor_name =
    pickText(header.contractor_name, project.contractor_name)
    || header.contractor_name;

  const lawyer_name =
    pickText(header.lawyer_name, project.lawyer_name) || header.lawyer_name;

  const accompanying_lawyer =
    pickText(header.accompanying_lawyer, project.accompanying_lawyer)
    || header.accompanying_lawyer;

  const stakeholders = mergeStakeholderPrefill(
    header.stakeholders,
    stakeholdersFromProject(project)
  );

  return {
    ...header,
    site_address,
    developer_name,
    developer_pm_name,
    contractor_name,
    lawyer_name,
    accompanying_lawyer,
    project_metadata: {
      ...project_metadata,
      site_address:
        pickText(project_metadata.site_address, site_address) || null,
      architect_name:
        pickText(
          project_metadata.architect_name,
          project.architect_name
        ) || null,
    },
    stakeholders,
  };
}

/** האם כדאי למלא אוטומטית מפרויקט (אין עדיין בעלי עניין / יזם). */
export function headerNeedsProjectPrefill(header: ReportHeaderFields): boolean {
  const hasStakeholder = header.stakeholders.some((item) => item.name?.trim());
  const hasDeveloper = Boolean(header.developer_name?.trim());
  const hasScheme = Boolean(header.project_metadata.scheme);
  return !hasStakeholder && !hasDeveloper && !hasScheme;
}

/** ממיר רשומת פרויקט גולמית (API / offline bundle) למקור prefill. */
export function projectPrefillSourceFromRecord(
  project: Record<string, unknown> | null | undefined
): ProjectPrefillSource | null {
  if (!project) {
    return null;
  }

  const housingUnits = project.housing_units_count;
  return {
    developer_name: pickText(String(project.developer_name ?? "")) || null,
    developer_pm_name:
      pickText(String(project.developer_pm_name ?? "")) || null,
    contractor_name: pickText(String(project.contractor_name ?? "")) || null,
    lawyer_name: pickText(String(project.lawyer_name ?? "")) || null,
    accompanying_lawyer:
      pickText(String(project.accompanying_lawyer ?? "")) || null,
    architect_name: pickText(String(project.architect_name ?? "")) || null,
    site_manager_name:
      pickText(String(project.site_manager_name ?? "")) || null,
    city: pickText(String(project.city ?? "")) || null,
    scheme: pickText(String(project.scheme ?? "")) || null,
    housing_units_count:
      typeof housingUnits === "number" && Number.isFinite(housingUnits)
        ? housingUnits
        : null,
    project_start_date:
      pickText(String(project.project_start_date ?? "")) || null,
    project_end_date: pickText(String(project.project_end_date ?? "")) || null,
    project_grace_end_date:
      pickText(String(project.project_grace_end_date ?? "")) || null,
    structure_documentation_date:
      pickText(String(project.structure_documentation_date ?? "")) || null,
    illustration_url:
      pickText(String(project.illustration_url ?? "")) || null,
    illustration_source_he:
      pickText(String(project.illustration_source_he ?? "")) || null,
  };
}
