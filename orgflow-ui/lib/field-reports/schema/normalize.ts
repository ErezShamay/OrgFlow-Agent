import {
  constructionProgressTitleHe,
} from "../construction-progress";
import {
  migrateLegacyFinishingBlocks,
  shouldMigrateLegacyFinishingBlocks,
} from "./migrate-legacy-finishing-blocks";
import {
  migrateLegacyProjectMetadataFromHeader,
  migrateLegacyStakeholdersFromHeader,
} from "./migrate-legacy-header";
import type {
  ChecklistBlock,
  ChecklistItem,
  ChecklistItemStatus,
  ColumnPresetKey,
  ConstructionStage,
  FindingRow,
  FindingsTableBlock,
  FixedTextBlock,
  FixedTextBlockKind,
  FreeTextBlock,
  ImageBlock,
  ProgressRow,
  ProgressTableBlock,
  ProjectMetadata,
  PublicAreaId,
  ReportBlock,
  Stakeholder,
  StakeholderRole,
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
  SupervisionReportMeta,
  SupplierRow,
  VisitReportDocument,
  VisitScope,
} from "./types";
import {
  CHECKLIST_ITEM_STATUSES,
  COLUMN_PRESET_KEYS,
  CONSTRUCTION_STAGES,
  FIXED_TEXT_BLOCK_KINDS,
  PROJECT_SCHEMES,
  STAKEHOLDER_ROLES,
  VISIT_SCOPES,
} from "./types";
import { normalizeOptionalTextInput } from "@/lib/validation/optional-field-display";

/** קלט גולמי לדוח ביקור - תואם תגובת API קיימת. */
export type RawVisitReportInput = {
  id: string;
  project_id?: string | null;
  visit_type: string;
  visit_date: string | Date;
  visit_type_label_he?: string | null;
  project_name?: string | null;
  header_fields?: Record<string, unknown> | null;
  lines?: unknown[] | null;
  catalog_version?: string | null;
  status?: string | null;
  organization_profile_snapshot?: Record<string, unknown> | null;
};

/**
 * מנרמל מטא-דאטה של פרויקט מ-header_fields / project_metadata.
 * שדות legacy (site_address וכו') נשמרים גם ב-header_fields_raw.
 */
export function normalizeProjectMetadata(
  raw: Record<string, unknown>,
  projectDefaults?: Partial<ProjectMetadata> | null
): ProjectMetadata {
  const legacy = migrateLegacyProjectMetadataFromHeader(raw);
  const nested = normalizeNestedProjectMetadata(raw.project_metadata);

  return {
    ...(projectDefaults ?? {}),
    ...legacy,
    ...nested,
  };
}

/**
 * מנרמל stakeholders - מערך מפורש + מיגרציה משדות legacy.
 * אין הסרה של שדות legacy מה-raw.
 */
export function normalizeStakeholders(
  raw: Record<string, unknown>
): Stakeholder[] {
  const explicit = normalizeStakeholderArray(raw.stakeholders);
  const byRole = new Map<StakeholderRole, Stakeholder>();

  for (const stakeholder of migrateLegacyStakeholdersFromHeader(raw)) {
    byRole.set(stakeholder.role, stakeholder);
  }

  for (const stakeholder of explicit) {
    byRole.set(stakeholder.role, stakeholder);
  }

  return Array.from(byRole.values());
}

/**
 * מנרמל בלוקי טקסט קבוע (boilerplate) מ-header_fields.
 */
export function normalizeFixedTextBlocks(
  raw: Record<string, unknown>,
  visitType: string
): FixedTextBlock[] {
  void visitType;

  if (Array.isArray(raw.fixed_text_blocks) && raw.fixed_text_blocks.length > 0) {
    return raw.fixed_text_blocks
      .map((item, index) => normalizeFixedTextBlock(item, index))
      .filter((block): block is FixedTextBlock => block !== null);
  }

  const blocks: FixedTextBlock[] = [];
  let sortOrder = 0;

  if (Array.isArray(raw.project_updates)) {
    const projectUpdates = raw.project_updates
      .map((item) => String(item).trim())
      .filter(Boolean);
    if (projectUpdates.length > 0) {
      blocks.push({
        id: "legacy-project-updates",
        kind: "custom",
        title_he: "עדכונים לפרויקט",
        body_he: projectUpdates.join("\n"),
        enabled: true,
        sort_order: sortOrder++,
      });
    }
  }

  if (typeof raw.winter_recommendations === "string") {
    const winterText = raw.winter_recommendations.trim();
    if (winterText) {
      blocks.push({
        id: "legacy-winter-recommendations",
        kind: "winter_recommendations",
        title_he: "המלצות חורף / עונת גשמים",
        body_he: winterText,
        enabled: true,
        sort_order: sortOrder++,
      });
    }
  }

  if (Array.isArray(raw.contractor_notes)) {
    const contractorNotes = raw.contractor_notes
      .map((item) => String(item).trim())
      .filter(Boolean);
    if (contractorNotes.length > 0) {
      blocks.push({
        id: "legacy-contractor-notes",
        kind: "agreement_notes",
        title_he: "הערות נוספות לקבלן",
        body_he: contractorNotes.join("\n"),
        enabled: true,
        sort_order: sortOrder++,
      });
    }
  }

  return blocks;
}

/**
 * מנרמל blocks[] - מ-header_fields.blocks או ממיר מ-construction_progress / lines.
 */
export function normalizeReportBlocks(
  raw: Record<string, unknown>,
  visitType: string,
  reportLines?: unknown[] | null
): ReportBlock[] {
  if (Array.isArray(raw.blocks) && raw.blocks.length > 0) {
    const normalized = raw.blocks
      .map((item, index) => normalizeReportBlock(item, index, visitType))
      .filter((block): block is ReportBlock => block !== null);

    if (
      shouldMigrateLegacyFinishingBlocks(
        visitType,
        raw,
        normalized,
        reportLines
      )
    ) {
      return migrateLegacyFinishingBlocks(raw, reportLines, normalized);
    }

    return normalized;
  }

  if (
    visitType === "FINISHING_APARTMENTS"
    && shouldMigrateLegacyFinishingBlocks(visitType, raw, [], reportLines)
  ) {
    return migrateLegacyFinishingBlocks(raw, reportLines);
  }

  const blocks: ReportBlock[] = [];
  let sortOrder = 0;

  if (Array.isArray(raw.construction_progress)) {
    const progressRows = raw.construction_progress
      .map((item, index) => normalizeProgressRowFromRaw(item, index))
      .filter((row) => row.description || row.status || row.completion_date);

    if (progressRows.length > 0) {
      blocks.push({
        id: "legacy-progress-table",
        kind: "progress_table",
        title_he: constructionProgressTitleHe(visitType),
        column_preset: "progress",
        rows: progressRows,
        sort_order: sortOrder++,
      });
    }
  }

  const lines = Array.isArray(reportLines) ? reportLines : [];
  if (lines.length > 0) {
    blocks.push({
      id: "legacy-findings-table",
      kind: "findings_table",
      title_he: "ממצאים / עבודות",
      column_preset: defaultFindingsColumnPreset(visitType),
      rows: lines
        .map((line, index) => normalizeFindingRow(line, index))
        .filter((row): row is FindingRow => row !== null),
      sort_order: sortOrder++,
    });
  }

  return blocks;
}

/**
 * aggregator - מנרמל דוח ביקור שלם ל-VisitReportDocument.
 * שדות legacy נשמרים ב-header_fields_raw ללא שינוי.
 */
export function normalizeVisitReportDocument(
  report: RawVisitReportInput,
  options?: { projectDefaults?: Partial<ProjectMetadata> | null }
): VisitReportDocument {
  const headerFields = { ...(report.header_fields ?? {}) };
  const lines = normalizeFindingRows(report.lines);

  return {
    id: report.id,
    project_id: stringField(report.project_id),
    visit_type: report.visit_type,
    visit_date: formatVisitDate(report.visit_date),
    visit_type_label_he: nullableString(report.visit_type_label_he),
    project_name: nullableString(report.project_name),
    project_metadata: normalizeProjectMetadata(
      headerFields,
      options?.projectDefaults
    ),
    stakeholders: normalizeStakeholders(headerFields),
    main_suppliers: normalizeMainSuppliers(headerFields),
    fixed_text_blocks: normalizeFixedTextBlocks(
      headerFields,
      report.visit_type
    ),
    blocks: normalizeReportBlocks(
      headerFields,
      report.visit_type,
      report.lines
    ),
    header_fields_raw: headerFields,
    lines,
    catalog_version: nullableString(report.catalog_version),
    status: nullableString(report.status),
    organization_profile_snapshot:
      report.organization_profile_snapshot ?? null,
  };
}

export function normalizeMainSuppliers(raw: Record<string, unknown>): SupplierRow[] {
  if (!Array.isArray(raw.main_suppliers)) {
    return [];
  }

  return raw.main_suppliers
    .map((item, index) => normalizeSupplierRow(item, index))
    .filter((row): row is SupplierRow => row !== null);
}

function normalizeNestedProjectMetadata(value: unknown): ProjectMetadata {
  if (!value || typeof value !== "object") {
    return {};
  }

  const raw = value as Record<string, unknown>;
  const metadata: ProjectMetadata = {};

  if (isProjectScheme(raw.scheme)) {
    metadata.scheme = raw.scheme;
  }

  assignOptionalString(metadata, "scheme_label_he", raw.scheme_label_he);
  assignOptionalString(metadata, "project_start_date", raw.project_start_date);
  assignOptionalString(metadata, "project_end_date", raw.project_end_date);
  assignOptionalString(
    metadata,
    "project_grace_end_date",
    raw.project_grace_end_date
  );
  assignOptionalString(
    metadata,
    "structure_documentation_date",
    raw.structure_documentation_date
  );
  assignOptionalString(metadata, "addressee_label_he", raw.addressee_label_he);
  assignOptionalString(metadata, "architect_name", raw.architect_name);
  assignOptionalString(metadata, "gantt_forecast", raw.gantt_forecast);
  assignOptionalString(metadata, "site_address", raw.site_address);
  assignOptionalString(
    metadata,
    "illustration_caption_he",
    raw.illustration_caption_he
  );
  assignOptionalString(
    metadata,
    "illustration_source_he",
    raw.illustration_source_he
  );
  assignOptionalString(metadata, "illustration_url", raw.illustration_url);
  assignOptionalString(metadata, "tenant_changes_notes", raw.tenant_changes_notes);

  if (
    typeof raw.housing_units_count === "number" &&
    Number.isFinite(raw.housing_units_count)
  ) {
    metadata.housing_units_count = raw.housing_units_count;
  }

  return metadata;
}

function normalizeStakeholderArray(value: unknown): Stakeholder[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item, index) => normalizeStakeholder(item, index))
    .filter((row): row is Stakeholder => row !== null);
}

function normalizeStakeholder(value: unknown, index: number): Stakeholder | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;
  const role = raw.role;
  if (typeof role !== "string" || !isStakeholderRole(role)) {
    return null;
  }

  const name = stringField(raw.name);
  if (!name) {
    return null;
  }

  return {
    id: stringField(raw.id, `stakeholder-${index}`),
    role,
    name,
    label_he: nullableString(raw.label_he),
  };
}

function normalizeSupplierRow(value: unknown, index: number): SupplierRow | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;
  const categoryHe = stringField(raw.category_he);
  const vendorName = stringField(raw.vendor_name);

  if (!categoryHe && !vendorName) {
    return null;
  }

  return {
    id: stringField(raw.id, `supplier-${index}`),
    category_he: categoryHe,
    vendor_name: vendorName,
  };
}

function normalizeFixedTextBlock(
  value: unknown,
  index: number
): FixedTextBlock | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;
  const kind = raw.kind;
  if (typeof kind !== "string" || !isFixedTextBlockKind(kind)) {
    return null;
  }

  const bodyHe = stringField(raw.body_he);
  if (!bodyHe) {
    return null;
  }

  return {
    id: stringField(raw.id, `fixed-text-${index}`),
    kind,
    title_he: nullableString(raw.title_he),
    body_he: bodyHe,
    enabled: raw.enabled !== false,
    sort_order:
      typeof raw.sort_order === "number" ? raw.sort_order : index,
  };
}

function normalizeReportBlock(
  value: unknown,
  index: number,
  visitType: string
): ReportBlock | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;
  const kind = raw.kind;

  const base = {
    id: stringField(raw.id, `block-${index}`),
    title_he: stringField(raw.title_he, defaultBlockTitle(kind, visitType)),
    sort_order: typeof raw.sort_order === "number" ? raw.sort_order : index,
  };

  switch (kind) {
    case "progress_table":
      return normalizeProgressTableBlock(raw, base);
    case "findings_table":
      return normalizeFindingsTableBlock(raw, base, visitType);
    case "checklist":
      return normalizeChecklistBlock(raw, base);
    case "supervision_checklist":
      return normalizeSupervisionChecklistBlock(raw, base);
    case "free_text":
      return normalizeFreeTextBlock(raw, base);
    case "image":
      return normalizeImageBlock(raw, base);
    default:
      return null;
  }
}

function normalizeProgressTableBlock(
  raw: Record<string, unknown>,
  base: { id: string; title_he: string; sort_order: number }
): ProgressTableBlock {
  return {
    ...base,
    kind: "progress_table",
    column_preset: normalizeColumnPreset(raw.column_preset, "progress"),
    rows: normalizeProgressRows(raw.rows),
  };
}

function normalizeFindingsTableBlock(
  raw: Record<string, unknown>,
  base: { id: string; title_he: string; sort_order: number },
  visitType: string
): FindingsTableBlock {
  return {
    ...base,
    kind: "findings_table",
    column_preset: normalizeColumnPreset(
      raw.column_preset,
      defaultFindingsColumnPreset(visitType)
    ),
    rows: normalizeFindingRows(raw.rows),
  };
}

function normalizeChecklistBlock(
  raw: Record<string, unknown>,
  base: { id: string; title_he: string; sort_order: number }
): ChecklistBlock {
  return {
    ...base,
    kind: "checklist",
    items: normalizeChecklistItems(raw.items),
  };
}

function normalizeSupervisionChecklistBlock(
  raw: Record<string, unknown>,
  base: { id: string; title_he: string; sort_order: number }
): SupervisionChecklistBlock | null {
  const constructionStage = raw.construction_stage;
  const visitScope = raw.visit_scope;

  if (
    typeof constructionStage !== "string" ||
    !isConstructionStage(constructionStage) ||
    typeof visitScope !== "string" ||
    !isVisitScope(visitScope)
  ) {
    return null;
  }

  return {
    ...base,
    kind: "supervision_checklist",
    construction_stage: constructionStage,
    visit_scope: visitScope,
    apartment_id: nullableString(raw.apartment_id),
    apartment_number: nullableString(raw.apartment_number),
    ad_hoc_apartment: raw.ad_hoc_apartment === true,
    public_area_id: normalizePublicAreaId(raw.public_area_id),
    items: normalizeSupervisionChecklistItems(raw.items),
  };
}

/** מנרמל supervision_meta מ-header_fields (§10.1). */
export function normalizeSupervisionMeta(
  raw: Record<string, unknown>
): SupervisionReportMeta | null {
  const nested = raw.supervision_meta;
  const source =
    nested && typeof nested === "object"
      ? (nested as Record<string, unknown>)
      : raw;

  const constructionStage = source.construction_stage;
  const visitScope = source.visit_scope;

  if (
    typeof constructionStage !== "string" ||
    !isConstructionStage(constructionStage) ||
    typeof visitScope !== "string" ||
    !isVisitScope(visitScope)
  ) {
    return null;
  }

  return {
    ...(typeof source.document_type === "string" &&
    (source.document_type === "weekly_inspection" ||
      source.document_type === "handover_protocol")
      ? { document_type: source.document_type }
      : {}),
    ...(source.inspect_mode === "standard" || source.inspect_mode === "quick"
      ? { inspect_mode: source.inspect_mode }
      : {}),
    construction_stage: constructionStage,
    visit_scope: visitScope,
    apartment_id: nullableString(source.apartment_id),
    apartment_number: nullableString(source.apartment_number),
    owner_name: nullableString(source.owner_name),
    ad_hoc_apartment: source.ad_hoc_apartment === true,
    public_area_id: normalizePublicAreaId(source.public_area_id),
    public_area_label_he: nullableString(source.public_area_label_he),
  };
}

function normalizeFreeTextBlock(
  raw: Record<string, unknown>,
  base: { id: string; title_he: string; sort_order: number }
): FreeTextBlock {
  return {
    ...base,
    kind: "free_text",
    body_he: stringField(raw.body_he),
  };
}

function normalizeImageBlock(
  raw: Record<string, unknown>,
  base: { id: string; title_he: string; sort_order: number }
): ImageBlock {
  return {
    ...base,
    kind: "image",
    caption_he: nullableString(raw.caption_he),
    image_url: nullableString(raw.image_url),
    storage_path: nullableString(raw.storage_path),
  };
}

function normalizeProgressRows(value: unknown): ProgressRow[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item, index) => {
      if (!item || typeof item !== "object") {
        return normalizeProgressRow({}, index);
      }
      return normalizeProgressRow(item as Record<string, unknown>, index);
    })
    .filter((row) => row.description || row.status || row.completion_date);
}

function normalizeProgressRowFromRaw(
  value: unknown,
  index: number
): ProgressRow {
  if (!value || typeof value !== "object") {
    return normalizeProgressRow({}, index);
  }
  return normalizeProgressRow(value as Record<string, unknown>, index);
}

function normalizeProgressRow(
  value: Record<string, unknown> | { description: string; status: string; completion_date: string },
  index: number
): ProgressRow {
  return {
    id: stringField("id" in value ? value.id : undefined, `progress-row-${index}`),
    description: stringField(value.description),
    status: stringField(value.status),
    completion_date: stringField(value.completion_date),
    sort_order:
      "sort_order" in value && typeof value.sort_order === "number"
        ? value.sort_order
        : index,
  };
}

function normalizeFindingRows(value: unknown): FindingRow[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item, index) => normalizeFindingRow(item, index))
    .filter((row): row is FindingRow => row !== null);
}

function normalizeFindingRow(value: unknown, index: number): FindingRow | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;
  const id = stringField(raw.id, `line-${index}`);

  return {
    id,
    location: nullableString(raw.location),
    trade: nullableString(raw.trade),
    status: nullableString(raw.status),
    description: nullableString(raw.description),
    notes: nullableString(raw.notes),
    severity: nullableString(raw.severity),
    standard_ref: nullableString(raw.standard_ref),
    catalog_reference_id: nullableString(raw.catalog_reference_id),
    issue_id: nullableString(raw.issue_id),
    group_key: nullableString(raw.group_key),
    group_label_he: nullableString(raw.group_label_he),
    block_id: nullableString(raw.block_id),
    linked_issue_id: nullableString(raw.linked_issue_id),
    sort_order:
      typeof raw.sort_order === "number" ? raw.sort_order : index,
    has_photo: raw.has_photo === true,
    photo_ids: normalizePhotoIds(raw.photo_ids),
  };
}

function normalizeChecklistItems(value: unknown): ChecklistItem[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const items: ChecklistItem[] = [];

  for (const [index, item] of value.entries()) {
    if (!item || typeof item !== "object") {
      continue;
    }
    const raw = item as Record<string, unknown>;
    const labelHe = stringField(raw.label_he);
    if (!labelHe) {
      continue;
    }

    items.push({
      id: stringField(raw.id, `checklist-item-${index}`),
      label_he: labelHe,
      checked: raw.checked === true,
      notes: nullableString(raw.notes) ?? undefined,
      sort_order:
        typeof raw.sort_order === "number" ? raw.sort_order : index,
    });
  }

  return items;
}

function normalizeSupervisionChecklistItems(
  value: unknown
): SupervisionChecklistItem[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const items: SupervisionChecklistItem[] = [];

  for (const [index, item] of value.entries()) {
    if (!item || typeof item !== "object") {
      continue;
    }

    const raw = item as Record<string, unknown>;
    const isCustom = raw.is_custom === true;
    const issueNameHe = stringField(raw.issue_name_he);
    const catalogIssueId = stringField(raw.catalog_issue_id);
    const standardRef = stringField(raw.standard_ref);

    if (!issueNameHe && !isCustom) {
      continue;
    }

    if (!isCustom && (!catalogIssueId || !standardRef)) {
      continue;
    }

    const status = raw.status;
    const normalizedStatus: ChecklistItemStatus =
      typeof status === "string" && isChecklistItemStatus(status)
        ? status
        : "UNCHECKED";

    items.push({
      id: stringField(raw.id, `checklist-item-${index}`),
      catalog_issue_id: catalogIssueId,
      issue_name_he: issueNameHe,
      category_id: stringField(
        raw.category_id,
        isCustom ? "custom-items" : ""
      ),
      category_name_he: stringField(
        raw.category_name_he,
        isCustom ? "פריטים מותאמים" : ""
      ),
      top_family: stringField(raw.top_family, isCustom ? "CUSTOM" : ""),
      standard_ref: standardRef,
      severity: nullableString(raw.severity),
      status: normalizedStatus,
      notes: nullableString(raw.notes),
      photo_ids: normalizeChecklistPhotoIds(raw.photo_ids),
      linked_line_id: nullableString(raw.linked_line_id),
      sort_order:
        typeof raw.sort_order === "number" ? raw.sort_order : index,
      ...(raw.hidden === true ? { hidden: true } : {}),
      ...(isCustom ? { is_custom: true } : {}),
    });
  }

  return items;
}

function normalizeChecklistPhotoIds(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter(Boolean)
    .slice(0, 3);
}

function normalizePublicAreaId(value: unknown): PublicAreaId | null {
  const text = stringField(value);
  if (!text) {
    return null;
  }

  const match = (
    [
      "LOBBY",
      "WET_ROOMS",
      "BALCONY_ROOF",
      "PARKING",
      "ELEVATOR_STAIRS",
      "OUTDOOR",
    ] as const
  ).find((id) => id === text);

  return match ?? null;
}

function isConstructionStage(value: string): value is ConstructionStage {
  return (CONSTRUCTION_STAGES as readonly string[]).includes(value);
}

function isVisitScope(value: string): value is VisitScope {
  return (VISIT_SCOPES as readonly string[]).includes(value);
}

function isChecklistItemStatus(value: string): value is ChecklistItemStatus {
  return (CHECKLIST_ITEM_STATUSES as readonly string[]).includes(value);
}

function normalizePhotoIds(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }

  const ids = value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter(Boolean)
    .slice(0, 5);

  return ids.length > 0 ? ids : undefined;
}

function defaultFindingsColumnPreset(visitType: string): ColumnPresetKey {
  if (visitType === "FINISHING_APARTMENTS") {
    return "finishing";
  }
  if (visitType === "STRUCTURE_SITE") {
    return "simple";
  }
  return "rich";
}

function defaultBlockTitle(kind: unknown, visitType: string): string {
  if (kind === "progress_table") {
    return constructionProgressTitleHe(visitType);
  }
  if (kind === "findings_table") {
    return "ממצאים / עבודות";
  }
  return "";
}

function normalizeColumnPreset(
  value: unknown,
  fallback: ColumnPresetKey
): ColumnPresetKey {
  if (typeof value === "string" && isColumnPresetKey(value)) {
    return value;
  }
  return fallback;
}

function isProjectScheme(value: unknown): value is ProjectMetadata["scheme"] {
  return (
    typeof value === "string" &&
    (PROJECT_SCHEMES as readonly string[]).includes(value)
  );
}

function isStakeholderRole(value: string): value is StakeholderRole {
  return (STAKEHOLDER_ROLES as readonly string[]).includes(value);
}

function isFixedTextBlockKind(value: string): value is FixedTextBlockKind {
  return (FIXED_TEXT_BLOCK_KINDS as readonly string[]).includes(value);
}

function isColumnPresetKey(value: string): value is ColumnPresetKey {
  return (COLUMN_PRESET_KEYS as readonly string[]).includes(value);
}

function assignOptionalString(
  target: ProjectMetadata,
  key: keyof ProjectMetadata,
  value: unknown
): void {
  const text = stringField(value);
  if (text) {
    (target as Record<string, string>)[key] = text;
  }
}

function stringField(value: unknown, fallback = ""): string {
  if (typeof value === "string") {
    const normalized = normalizeOptionalTextInput(value);
    return normalized || fallback;
  }
  if (value === null || value === undefined) {
    return fallback;
  }
  return normalizeOptionalTextInput(String(value));
}

function nullableString(value: unknown): string | null {
  const text = stringField(value);
  return text || null;
}

function formatVisitDate(value: string | Date): string {
  if (value instanceof Date) {
    return value.toISOString().slice(0, 10);
  }
  return String(value);
}
