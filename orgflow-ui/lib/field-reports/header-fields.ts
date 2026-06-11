import {
  normalizeConstructionProgressRows,
  serializeConstructionProgressRows,
  type ConstructionProgressRow,
} from "./construction-progress";
import {
  DEFAULT_CONTRACTOR_NOTES_HE,
  DEFAULT_PROJECT_UPDATES_HE,
  DEFAULT_WINTER_RECOMMENDATIONS_HE,
} from "./pdf-block-defaults";
import {
  dualWriteHeaderBlocksAndProgress,
  findProgressTableBlock,
  normalizeBlocksFromHeader,
  progressRowsToConstructionProgress,
  serializeBlocksForApi,
} from "./schema/blocks-storage";
import {
  normalizeMainSuppliers,
  normalizeProjectMetadata,
  normalizeStakeholders,
} from "./schema";
import {
  resolveFixedTextBlocksFromHeader,
  resolveIncludeFixedTextBlocks,
  syncLegacyFieldsFromFixedTextBlocks,
} from "./schema/fixed-text-inject";
import type {
  FixedTextBlock,
  ProjectMetadata,
  ReportBlock,
  Stakeholder,
  StakeholderRole,
  SupplierRow,
} from "./schema/types";

export type {
  FixedTextBlock,
  ProjectMetadata,
  ReportBlock,
  Stakeholder,
  SupplierRow,
};

/** שדות legacy בכותרת - נשמרים לתאימות API ו-PDF קיים. */
export type ReportHeaderLegacyFields = {
  site_address: string;
  developer_name: string;
  developer_pm_name: string;
  lawyer_name: string;
  accompanying_lawyer: string;
  contractor_name: string;
  project_updates: string[];
  winter_recommendations: string;
  contractor_notes: string[];
  inspector_title: string;
  inspector_license: string;
  construction_progress: ConstructionProgressRow[];
};

/**
 * שדות כותרת דוח - legacy + מבנה חדש (FR-1.1).
 * העריכה ב-UI עדיין יכולה לגעת בשדות legacy; נורמליזציה מסנכרנת ל-stakeholders.
 */
export type ReportHeaderFields = ReportHeaderLegacyFields & {
  project_metadata: ProjectMetadata;
  stakeholders: Stakeholder[];
  main_suppliers: SupplierRow[];
  /** בלוקי גוף הדוח - נשמרים ב-header_fields.blocks (FR-2.1). */
  blocks: ReportBlock[];
  /** טקסטים קבועים (disclaimers, חורף) - FR-4.2. */
  fixed_text_blocks: FixedTextBlock[];
  /** מתג ראשי - האם לכלול boilerplate ב-PDF. */
  include_fixed_text_blocks: boolean;
};

export type NormalizeHeaderFieldsOptions = {
  /** שורות דוח - ליצירת findings block כשאין blocks (derive read-only). */
  lines?: unknown[] | null;
  /** תאריך ביקור - להפעלת המלצות חורף עונתיות. */
  visitDate?: string;
};

const STAKEHOLDER_LEGACY_FIELD_MAP: ReadonlyArray<{
  role: StakeholderRole;
  field: keyof Pick<
    ReportHeaderLegacyFields,
    | "developer_name"
    | "developer_pm_name"
    | "contractor_name"
    | "lawyer_name"
    | "accompanying_lawyer"
  >;
}> = [
  { role: "developer", field: "developer_name" },
  { role: "project_manager", field: "developer_pm_name" },
  { role: "contractor", field: "contractor_name" },
  { role: "lawyer_tenants", field: "lawyer_name" },
  { role: "lawyer_accompanying", field: "accompanying_lawyer" },
];

export function normalizeHeaderFields(
  fields: Record<string, unknown>,
  visitType = "STRUCTURE_SITE",
  options?: NormalizeHeaderFieldsOptions
): ReportHeaderFields {
  const project_metadata = normalizeProjectMetadata(fields);
  const stakeholders = normalizeStakeholders(fields);
  const main_suppliers = normalizeMainSuppliers(fields);

  const legacy = normalizeLegacyHeaderStrings(
    fields,
    visitType,
    project_metadata,
    stakeholders
  );

  const fixed_text_blocks = resolveFixedTextBlocksFromHeader(
    fields,
    options?.visitDate
  );
  const include_fixed_text_blocks = resolveIncludeFixedTextBlocks(
    fields,
    fixed_text_blocks
  );
  const legacySynced = syncLegacyFieldsFromFixedTextBlocks(
    fixed_text_blocks,
    {
      winter_recommendations: legacy.winter_recommendations,
      contractor_notes: legacy.contractor_notes,
      project_updates: legacy.project_updates,
    },
    include_fixed_text_blocks
  );
  const legacyWithFixedText: ReportHeaderLegacyFields = {
    ...legacy,
    ...legacySynced,
  };

  const blocks = normalizeBlocksFromHeader(fields, visitType, {
    lines: options?.lines ?? null,
  });
  const synced = dualWriteHeaderBlocksAndProgress(
    blocks,
    legacyWithFixedText.construction_progress,
    visitType
  );

  return {
    ...legacyWithFixedText,
    construction_progress: synced.construction_progress,
    project_metadata: {
      ...project_metadata,
      site_address: legacy.site_address || project_metadata.site_address || null,
      architect_name:
        legacyArchitectName(stakeholders, project_metadata) || null,
    },
    stakeholders,
    main_suppliers,
    blocks: synced.blocks,
    fixed_text_blocks,
    include_fixed_text_blocks,
  };
}

export function serializeHeaderFieldsForApi(
  fields: ReportHeaderFields
): Record<string, unknown> {
  const stakeholders = mergeStakeholdersForApi(fields);
  const project_metadata = serializeProjectMetadataForApi(fields, stakeholders);

  const payload: Record<string, unknown> = {
    site_address: fields.site_address || null,
    developer_name: fields.developer_name || null,
    developer_pm_name: fields.developer_pm_name || null,
    lawyer_name: fields.lawyer_name || null,
    accompanying_lawyer: fields.accompanying_lawyer || null,
    contractor_name: fields.contractor_name || null,
    project_updates: cleanStringList(fields.project_updates),
    winter_recommendations: fields.winter_recommendations.trim(),
    contractor_notes: cleanStringList(fields.contractor_notes),
    inspector_title: fields.inspector_title || null,
    inspector_license: fields.inspector_license || null,
    construction_progress: serializeConstructionProgressRows(
      fields.construction_progress
    ),
    blocks: serializeBlocksForApi(fields.blocks),
    fixed_text_blocks: fields.fixed_text_blocks.map(serializeFixedTextBlockForApi),
    include_fixed_text_blocks: fields.include_fixed_text_blocks,
    project_metadata,
    stakeholders: stakeholders.map(serializeStakeholderForApi),
    main_suppliers: fields.main_suppliers.map(serializeSupplierForApi),
  };

  syncLegacyMetadataTopLevel(payload, project_metadata);

  return payload;
}

export function cleanStringList(values: string[]): string[] {
  return values.map((item) => item.trim()).filter(Boolean);
}

/**
 * מעדכן stakeholders / ספקים ומסנכרן שדות legacy + API (FR-1.3).
 */
/**
 * מעדכן התקדמות בנייה ומסנכרן לבלוק progress_table (dual-write FR-2.1).
 */
export function patchHeaderFieldsConstructionProgress(
  fields: ReportHeaderFields,
  construction_progress: ConstructionProgressRow[],
  visitType: string
): ReportHeaderFields {
  const synced = dualWriteHeaderBlocksAndProgress(
    fields.blocks,
    construction_progress,
    visitType
  );

  return {
    ...fields,
    construction_progress: synced.construction_progress,
    blocks: synced.blocks,
  };
}

/**
 * מעדכן blocks[] ומסנכרן construction_progress מבלוק ההתקדמות (dual-write FR-2.1).
 */
export function patchHeaderFieldsFixedTextBlocks(
  fields: ReportHeaderFields,
  update: {
    fixed_text_blocks: FixedTextBlock[];
    include_fixed_text_blocks?: boolean;
  },
  visitType: string,
  visitDate?: string
): ReportHeaderFields {
  const payload = serializeHeaderFieldsForApi({
    ...fields,
    fixed_text_blocks: update.fixed_text_blocks,
    include_fixed_text_blocks:
      update.include_fixed_text_blocks ?? fields.include_fixed_text_blocks,
  });
  payload.fixed_text_blocks = update.fixed_text_blocks.map(
    serializeFixedTextBlockForApi
  );
  if (update.include_fixed_text_blocks !== undefined) {
    payload.include_fixed_text_blocks = update.include_fixed_text_blocks;
  }

  return normalizeHeaderFields(payload, visitType, { visitDate });
}

export function patchHeaderFieldsBlocks(
  fields: ReportHeaderFields,
  blocks: ReportBlock[],
  visitType: string
): ReportHeaderFields {
  const progressBlock = findProgressTableBlock(blocks);
  const construction_progress = progressBlock
    ? progressRowsToConstructionProgress(progressBlock.rows)
    : fields.construction_progress;

  const synced = dualWriteHeaderBlocksAndProgress(
    blocks,
    construction_progress,
    visitType
  );

  return {
    ...fields,
    blocks: synced.blocks,
    construction_progress: synced.construction_progress,
  };
}

export function patchHeaderFieldsStakeholders(
  fields: ReportHeaderFields,
  update: {
    stakeholders: Stakeholder[];
    main_suppliers?: SupplierRow[];
  },
  visitType: string
): ReportHeaderFields {
  const stakeholders = update.stakeholders;
  const syncedLegacy: ReportHeaderFields = {
    ...fields,
    stakeholders,
    main_suppliers: update.main_suppliers ?? fields.main_suppliers,
    developer_name: stakeholderName(stakeholders, "developer"),
    developer_pm_name: stakeholderName(stakeholders, "project_manager"),
    contractor_name: stakeholderName(stakeholders, "contractor"),
    lawyer_name: stakeholderName(stakeholders, "lawyer_tenants"),
    accompanying_lawyer: stakeholderName(stakeholders, "lawyer_accompanying"),
    project_metadata: {
      ...fields.project_metadata,
      architect_name:
        stakeholderName(stakeholders, "architect") ||
        fields.project_metadata.architect_name ||
        null,
    },
  };

  return normalizeHeaderFields(
    serializeHeaderFieldsForApi(syncedLegacy),
    visitType
  );
}

function normalizeLegacyHeaderStrings(
  fields: Record<string, unknown>,
  visitType: string,
  project_metadata: ProjectMetadata,
  stakeholders: Stakeholder[]
): ReportHeaderLegacyFields {
  return {
    site_address:
      stringField(fields.site_address) ||
      stringField(project_metadata.site_address),
    developer_name:
      stringField(fields.developer_name) ||
      stakeholderName(stakeholders, "developer"),
    developer_pm_name:
      stringField(fields.developer_pm_name ?? fields.contractor_name) ||
      stakeholderName(stakeholders, "project_manager"),
    lawyer_name:
      stringField(fields.lawyer_name) ||
      stakeholderName(stakeholders, "lawyer_tenants"),
    accompanying_lawyer:
      stringField(fields.accompanying_lawyer) ||
      stakeholderName(stakeholders, "lawyer_accompanying"),
    contractor_name:
      stringField(fields.contractor_name) ||
      stakeholderName(stakeholders, "contractor"),
    project_updates: stringListField(
      fields.project_updates,
      DEFAULT_PROJECT_UPDATES_HE
    ),
    winter_recommendations: stringField(
      fields.winter_recommendations,
      DEFAULT_WINTER_RECOMMENDATIONS_HE
    ),
    contractor_notes: stringListField(
      fields.contractor_notes,
      DEFAULT_CONTRACTOR_NOTES_HE
    ),
    inspector_title: stringField(fields.inspector_title),
    inspector_license: stringField(fields.inspector_license),
    construction_progress: normalizeConstructionProgressRows(
      fields.construction_progress,
      visitType
    ),
  };
}

function mergeStakeholdersForApi(fields: ReportHeaderFields): Stakeholder[] {
  const byRole = new Map<StakeholderRole, Stakeholder>();

  for (const stakeholder of fields.stakeholders) {
    byRole.set(stakeholder.role, stakeholder);
  }

  for (const { role, field } of STAKEHOLDER_LEGACY_FIELD_MAP) {
    const name = fields[field].trim();
    if (name) {
      const existing = byRole.get(role);
      byRole.set(role, {
        id: existing?.id ?? `legacy-${role}`,
        role,
        name,
        label_he: existing?.label_he ?? null,
      });
      continue;
    }

    const existing = byRole.get(role);
    if (existing?.id.startsWith("legacy-")) {
      byRole.delete(role);
    }
  }

  const architectName =
    stringField(fields.project_metadata.architect_name) ||
    stakeholderName(Array.from(byRole.values()), "architect");
  if (architectName) {
    const existing = byRole.get("architect");
    byRole.set("architect", {
      id: existing?.id ?? "legacy-architect",
      role: "architect",
      name: architectName,
      label_he: existing?.label_he ?? null,
    });
  }

  return Array.from(byRole.values());
}

function serializeProjectMetadataForApi(
  fields: ReportHeaderFields,
  stakeholders: Stakeholder[]
): Record<string, unknown> {
  const metadata: Record<string, unknown> = {
    ...fields.project_metadata,
    site_address: fields.site_address || fields.project_metadata.site_address || null,
    architect_name:
      stringField(fields.project_metadata.architect_name) ||
      stakeholderName(stakeholders, "architect") ||
      null,
  };

  return omitEmptyMetadata(metadata);
}

function syncLegacyMetadataTopLevel(
  payload: Record<string, unknown>,
  project_metadata: Record<string, unknown>
): void {
  const metadataKeys = [
    "scheme",
    "scheme_label_he",
    "project_start_date",
    "project_end_date",
    "project_grace_end_date",
    "housing_units_count",
    "structure_documentation_date",
    "addressee_label_he",
    "gantt_forecast",
    "illustration_caption_he",
    "illustration_source_he",
    "illustration_url",
    "tenant_changes_notes",
    "architect_name",
  ] as const;

  for (const key of metadataKeys) {
    if (project_metadata[key] !== undefined && project_metadata[key] !== null) {
      payload[key] = project_metadata[key];
    }
  }
}

function serializeStakeholderForApi(
  stakeholder: Stakeholder
): Record<string, unknown> {
  return {
    id: stakeholder.id,
    role: stakeholder.role,
    name: stakeholder.name,
    label_he: stakeholder.label_he ?? null,
  };
}

function serializeSupplierForApi(supplier: SupplierRow): Record<string, unknown> {
  return {
    id: supplier.id,
    category_he: supplier.category_he,
    vendor_name: supplier.vendor_name,
  };
}

function serializeFixedTextBlockForApi(
  block: FixedTextBlock
): Record<string, unknown> {
  return {
    id: block.id,
    kind: block.kind,
    title_he: block.title_he ?? null,
    body_he: block.body_he,
    enabled: block.enabled,
    sort_order: block.sort_order ?? 0,
  };
}

function stakeholderName(
  stakeholders: Stakeholder[],
  role: StakeholderRole
): string {
  return stakeholders.find((item) => item.role === role)?.name ?? "";
}

function legacyArchitectName(
  stakeholders: Stakeholder[],
  project_metadata: ProjectMetadata
): string {
  return (
    stringField(project_metadata.architect_name) ||
    stakeholderName(stakeholders, "architect")
  );
}

function omitEmptyMetadata(
  metadata: Record<string, unknown>
): Record<string, unknown> {
  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(metadata)) {
    if (value === undefined || value === null) {
      continue;
    }
    if (typeof value === "string" && !value.trim()) {
      continue;
    }
    result[key] = value;
  }

  return result;
}

function stringField(value: unknown, fallback = ""): string {
  if (typeof value === "string") {
    return value;
  }
  if (value === null || value === undefined) {
    return fallback;
  }
  return String(value);
}

function stringListField(value: unknown, fallback: string[]): string[] {
  if (!Array.isArray(value)) {
    return [...fallback];
  }
  return value.map((item) => String(item));
}
