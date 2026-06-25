/**
 * סכמת דוחות שטח - ייצוא types (FR-0.1).
 */

export type {
  BlockColumnDef,
  BlockColumnId,
  ChecklistBlock,
  ChecklistItem,
  ColumnPresetKey,
  ColumnPresets,
  FindingRow,
  FixedTextBlock,
  FixedTextBlockKind,
  FreeTextBlock,
  ImageBlock,
  ProgressRow,
  ProgressTableBlock,
  ProjectMetadata,
  ProjectScheme,
  ReportBlock,
  ReportBlockBase,
  ReportBlockKind,
  FindingsTableBlock,
  Stakeholder,
  StakeholderRole,
  SupplierRow,
  VisitReportDocument,
} from "./types";

export {
  BLOCK_COLUMN_IDS,
  COLUMN_PRESET_KEYS,
  FIXED_TEXT_BLOCK_KINDS,
  PROJECT_SCHEMES,
  STAKEHOLDER_ROLES,
} from "./types";

export {
  migrateLegacyProjectMetadataFromHeader,
  migrateLegacyStakeholdersFromHeader,
} from "./migrate-legacy-header";

export {
  normalizeFixedTextBlocks,
  normalizeMainSuppliers,
  normalizeProjectMetadata,
  normalizeReportBlocks,
  normalizeStakeholders,
  normalizeVisitReportDocument,
  type RawVisitReportInput,
} from "./normalize";

export {
  COLUMN_PRESETS,
  getColumnPreset,
  getColumnPresetHeaders,
} from "./column-presets";

export {
  LEGACY_FINDINGS_BLOCK_ID,
  LEGACY_PROGRESS_BLOCK_ID,
  addBlock,
  constructionProgressToProgressRows,
  createEmptyBlockForKind,
  deriveFindingRowsFromReportLines,
  dualWriteHeaderBlocksAndProgress,
  findFindingsTableBlock,
  findProgressTableBlock,
  normalizeBlocksFromHeader,
  progressRowsToConstructionProgress,
  removeBlock,
  reorderBlocks,
  replaceProgressTableRows,
  resolveConstructionProgressFromBlocks,
  serializeBlocksForApi,
  updateBlock,
  type NormalizeBlocksOptions,
} from "./blocks-storage";

export {
  DEFAULT_FINISHING_CHECKLIST_BLOCK_ID,
  DEFAULT_FINISHING_CHECKLIST_TITLE_HE,
  FINISHING_CHECKLIST_ITEM_DEFS,
  defaultFinishingChecklistBlock,
  defaultFinishingChecklistItems,
} from "./checklist-presets";

export {
  buildFixedTextBlocksForNewReport,
  applyWinterSeasonToBlocks,
  createEmptyCustomFixedTextBlock,
  FIXED_TEXT_BLOCK_KIND_LABELS,
  isRemovableFixedTextBlock,
  isWinterSeasonDate,
  resolveFixedTextBlocksFromHeader,
  resolveIncludeFixedTextBlocks,
  syncLegacyFieldsFromFixedTextBlocks,
} from "./fixed-text-inject";

export {
  addChecklistItem,
  addCustomSupervisionItem,
  confirmChecklistItemDelete,
  createEmptyChecklistItem,
  createEmptyCustomSupervisionItem,
  CUSTOM_SUPERVISION_CATEGORY_ID,
  CUSTOM_SUPERVISION_CATEGORY_NAME_HE,
  CUSTOM_SUPERVISION_TOP_FAMILY,
  hiddenSupervisionCatalogItems,
  hideSupervisionCatalogItem,
  isSupervisionCatalogItem,
  isSupervisionCustomItem,
  removeChecklistItem,
  removeSupervisionCustomItem,
  restoreSupervisionCatalogItem,
  shouldConfirmFinishingChecklistItemDelete,
  shouldConfirmSupervisionChecklistItemDelete,
  updateChecklistItem,
  updateSupervisionChecklistItem,
  visibleSupervisionChecklistItems,
} from "./checklist-item-mutations";

export {
  DEFAULT_BLOCKS_BY_VISIT_TYPE,
  DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE,
  DEFAULT_SAFETY_DISCLAIMER_HE,
  DEFAULT_WINTER_RECOMMENDATIONS_HE,
  VISIT_TYPE_MIXED,
  defaultFixedTextBlocks,
  defaultProgressBlockTitleHe,
  defaultReportBlocksForVisitType,
} from "./block-defaults";
