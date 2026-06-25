/**
 * סכמת דוחות שטח - types מרכזיים (FR-0.1).
 * לוגיקת נורמליזציה / presets בקבצים נפרדים (FR-0.2, FR-0.4).
 */

/** סוגי פרויקט תמ"א כפי שמופיעים בדוחות הלקוח. */
export const PROJECT_SCHEMES = [
  "TAMA38_STRENGTHENING",
  "TAMA38_DEMOLITION_REBUILD",
  "TAMA38_RELOCATED_BUILD",
  "NEW_CONSTRUCTION",
] as const;

/** מזהה סוג פרויקט (חיזוק / הריסה ובניה / פינוי בינוי). */
export type ProjectScheme = (typeof PROJECT_SCHEMES)[number];

/**
 * מטא-דאטה של פרויקט בכותרת הדוח - תאריכים, יחידות דיור, הדמיה.
 * שדות אופציונליים לתמיכה בדוחות legacy חלקיים.
 */
export type ProjectMetadata = {
  scheme?: ProjectScheme | null;
  /** תווית עברית מחושבת, למשל: התחדשות עירונית - פרויקט חיזוק תמ"א */
  scheme_label_he?: string | null;
  project_start_date?: string | null;
  project_end_date?: string | null;
  project_grace_end_date?: string | null;
  housing_units_count?: number | null;
  structure_documentation_date?: string | null;
  addressee_label_he?: string | null;
  architect_name?: string | null;
  gantt_forecast?: string | null;
  site_address?: string | null;
  illustration_caption_he?: string | null;
  /** מקור התמונה, למשל: התמונה נלקחה מאתר אינטרנט "מדלן". */
  illustration_source_he?: string | null;
  /** URL להדמיית הפרויקט - נטען מפרטי הפרויקט (תמונה אחת). */
  illustration_url?: string | null;
  tenant_changes_notes?: string | null;
};

/** תפקידי בעלי עניין בדוח - ממופים משדות legacy ב-FR-0.2. */
export const STAKEHOLDER_ROLES = [
  "developer",
  "project_manager",
  "site_manager",
  "contractor",
  "lawyer_tenants",
  "lawyer_accompanying",
  "architect",
] as const;

/** תפקיד stakeholder בדוח. */
export type StakeholderRole = (typeof STAKEHOLDER_ROLES)[number];

/**
 * בעל עניין בדוח (יזם, עו"ד, קבלן וכו').
 * `id` יציב לעריכה ב-UI.
 */
export type Stakeholder = {
  id: string;
  role: StakeholderRole;
  name: string;
  label_he?: string | null;
};

/** שורת ספק עיקרי (קטגוריה + vendor) כמו בדוח ההגנה. */
export type SupplierRow = {
  id: string;
  category_he: string;
  vendor_name: string;
};

/** סוגי טקסטים קבועים (boilerplate) בגוף / כותרת הדוח. */
export const FIXED_TEXT_BLOCK_KINDS = [
  "safety_disclaimer",
  "non_conformance_disclaimer",
  "winter_recommendations",
  "agreement_notes",
  "custom",
] as const;

/** מזהה סוג בלוק טקסט קבוע. */
export type FixedTextBlockKind = (typeof FIXED_TEXT_BLOCK_KINDS)[number];

/**
 * בלוק טקסט קבוע - disclaimer בטיחות, אי-התאמה, המלצות חורף.
 */
export type FixedTextBlock = {
  id: string;
  kind: FixedTextBlockKind;
  title_he?: string | null;
  body_he: string;
  enabled: boolean;
  sort_order?: number;
};

/** preset עמודות לפי וריאציות מדוחות הלקוח. */
export const COLUMN_PRESET_KEYS = [
  "rich",
  "simple",
  "finishing",
  "progress",
  "structure",
] as const;

/** מפתח preset עמודות טבלה. */
export type ColumnPresetKey = (typeof COLUMN_PRESET_KEYS)[number];

/** מזהה עמודה בטבלת בלוק. */
export const BLOCK_COLUMN_IDS = [
  "location",
  "trade",
  "status",
  "description",
  "notes",
  "photos",
  "completion_date",
  "checklist_item",
] as const;

/** מזהה עמודה בודדת בבלוק. */
export type BlockColumnId = (typeof BLOCK_COLUMN_IDS)[number];

/** הגדרת עמודה בטבלת בלוק - כותרת עברית ורוחב אופציונלי. */
export type BlockColumnDef = {
  id: BlockColumnId;
  header_he: string;
  width?: number | string;
};

/**
 * מפת presets עמודות - ערכים מלאים יוגדרו ב-FR-0.4 (`column-presets.ts`).
 * FR-0.1 מגדיר רק את הצורה.
 */
export type ColumnPresets = Record<ColumnPresetKey, readonly BlockColumnDef[]>;

/** שורה בטבלת התקדמות (construction progress). */
export type ProgressRow = {
  id: string;
  description: string;
  status: string;
  completion_date: string;
  sort_order?: number;
};

/**
 * שורת ממצא - תואמת שורות `lines` קיימות + שדות קיבוץ (FR-3.1).
 */
export type FindingRow = {
  id: string;
  location?: string | null;
  trade?: string | null;
  status?: string | null;
  description?: string | null;
  notes?: string | null;
  severity?: string | null;
  standard_ref?: string | null;
  catalog_reference_id?: string | null;
  issue_id?: string | null;
  group_key?: string | null;
  group_label_he?: string | null;
  block_id?: string | null;
  linked_issue_id?: string | null;
  sort_order?: number;
  has_photo?: boolean;
  photo_ids?: string[];
};

/** פריט בצ'קליסט גמר (בעלים, חשמל, אינסטלציה וכו'). */
export type ChecklistItem = {
  id: string;
  label_he: string;
  checked: boolean;
  notes?: string | null;
  sort_order?: number;
};

/** שלבי בנייה לדוח מפקח בשטח. */
export const CONSTRUCTION_STAGES = [
  "STRUCTURE",
  "FINISHING",
  "MIXED",
] as const;

export type ConstructionStage = (typeof CONSTRUCTION_STAGES)[number];

/** היקף ביקור — דירה, שטחים ציבוריים, או מסירה (עתידי). */
export const VISIT_SCOPES = ["APARTMENT", "PUBLIC_AREA", "HANDOVER"] as const;

export type VisitScope = (typeof VISIT_SCOPES)[number];

/** סוג מסמך במודול — FIELD-REPORT-CHECKLISTS.md §2. */
export const FIELD_REPORT_DOCUMENT_TYPES = [
  "weekly_inspection",
  "handover_protocol",
] as const;

export type FieldReportDocumentType =
  (typeof FIELD_REPORT_DOCUMENT_TYPES)[number];

/** מצב סימון צ'קליסט מפקח — מהיר (V/X) או סטנדרטי (4 סטטוסים). */
export const INSPECT_MODES = ["standard", "quick"] as const;

export type InspectMode = (typeof INSPECT_MODES)[number];

/** סטטוס פריט בצ'קליסט מפקח. */
export const CHECKLIST_ITEM_STATUSES = [
  "UNCHECKED",
  "OK",
  "DEFECT",
  "NOT_APPLICABLE",
] as const;

export type ChecklistItemStatus = (typeof CHECKLIST_ITEM_STATUSES)[number];

/** היקף פריט בקטלוג supervision. */
export const CATALOG_ISSUE_SCOPES = [
  "APARTMENT",
  "PUBLIC_AREA",
  "BOTH",
] as const;

export type CatalogIssueScope = (typeof CATALOG_ISSUE_SCOPES)[number];

/** אזורים ציבוריים — נספח א' במפרט field-supervision-checklist. */
export const PUBLIC_AREA_DEFINITIONS = [
  { id: "LOBBY", label_he: "לובי / כניסה" },
  { id: "WET_ROOMS", label_he: "חדרים רטובים משותפים" },
  { id: "BALCONY_ROOF", label_he: "מרפסות / גג משותף" },
  { id: "PARKING", label_he: "חניון / מחסנים" },
  { id: "ELEVATOR_STAIRS", label_he: "מעליות / חדרי מדרגות" },
  { id: "OUTDOOR", label_he: "שטח חוץ / גינון" },
] as const;

export type PublicAreaDefinition = (typeof PUBLIC_AREA_DEFINITIONS)[number];

export type PublicAreaId = PublicAreaDefinition["id"];

/** מטא-דאטה לדוח מפקח בשטח (header_fields.supervision_meta). */
export type SupervisionReportMeta = {
  document_type?: FieldReportDocumentType;
  /** weekly_inspection → quick כברירת מחדל (V1). */
  inspect_mode?: InspectMode;
  construction_stage: ConstructionStage;
  visit_scope: VisitScope;
  apartment_id?: string | null;
  apartment_number?: string | null;
  owner_name?: string | null;
  ad_hoc_apartment?: boolean;
  public_area_id?: PublicAreaId | null;
  public_area_label_he?: string | null;
};

/** פריט קטלוג supervision (offline prep / seed). */
export type SupervisionCatalogIssue = {
  issue_id: string;
  issue_name_he: string;
  standard_ref: string;
  catalog_reference_id?: string | null;
  top_family: string;
  category_id: string;
  category_name_he: string;
  severity?: string | null;
  description?: string | null;
  scope: CatalogIssueScope;
  public_area_id?: PublicAreaId | null;
  allowed_stages: readonly ConstructionStage[];
};

export type SupervisionCatalog = {
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
  issues: SupervisionCatalogIssue[];
};

/** פריט בצ'קליסט מפקח — מעוגן לקטלוג supervision או מותאם ידנית. */
export type SupervisionChecklistItem = {
  id: string;
  catalog_issue_id: string;
  issue_name_he: string;
  category_id: string;
  category_name_he: string;
  top_family: string;
  standard_ref: string;
  severity?: string | null;
  status: ChecklistItemStatus;
  notes?: string | null;
  photo_ids: string[];
  linked_line_id?: string | null;
  sort_order: number;
  /** פריט קטלוג שלא רלוונטי לביקור — מוסתר מהדוח (לא נמחק מהקטלוג). */
  hidden?: boolean;
  /** פריט שנוסף ידנית על ידי הלקוח — ללא קישור לקטלוג. */
  is_custom?: boolean;
};

/** שדות משותפים לכל בלוק בגוף הדוח. */
export type ReportBlockBase = {
  id: string;
  title_he: string;
  sort_order?: number;
};

/** בלוק טבלת התקדמות - ממיר מ-`construction_progress[]` legacy. */
export type ProgressTableBlock = ReportBlockBase & {
  kind: "progress_table";
  column_preset: ColumnPresetKey;
  rows: ProgressRow[];
};

/** בלוק טבלת ממצאים - ממיר מ-`lines[]` legacy. */
export type FindingsTableBlock = ReportBlockBase & {
  kind: "findings_table";
  column_preset: ColumnPresetKey;
  rows: FindingRow[];
};

/** בלוק צ'קליסט גמר - דוחות FINISHING_APARTMENTS. */
export type ChecklistBlock = ReportBlockBase & {
  kind: "checklist";
  items: ChecklistItem[];
};

/** בלוק צ'קליסט מפקח — kind חדש (לא לשבור checklist גמר ישן). */
export type SupervisionChecklistBlock = ReportBlockBase & {
  kind: "supervision_checklist";
  construction_stage: ConstructionStage;
  visit_scope: VisitScope;
  apartment_id?: string | null;
  apartment_number?: string | null;
  ad_hoc_apartment?: boolean;
  public_area_id?: PublicAreaId | null;
  items: SupervisionChecklistItem[];
};

/** בלוק טקסט חופשי - המלצות, הערות נוספות. */
export type FreeTextBlock = ReportBlockBase & {
  kind: "free_text";
  body_he: string;
};

/** בלוק תמונה - הדמיית פרויקט. */
export type ImageBlock = ReportBlockBase & {
  kind: "image";
  caption_he?: string | null;
  image_url?: string | null;
  storage_path?: string | null;
};

/**
 * בלוק בגוף הדוח - discriminated union לפי `kind`.
 * תבנית אחת גמישה מבוססת רכיבים (`blocks[]`).
 */
export type ReportBlock =
  | ProgressTableBlock
  | FindingsTableBlock
  | ChecklistBlock
  | SupervisionChecklistBlock
  | FreeTextBlock
  | ImageBlock;

/** מזהה סוג בלוק בגוף הדוח. */
export type ReportBlockKind = ReportBlock["kind"];

/**
 * מסמך דוח ביקור - יעד הנורמליזציה (FR-0.2).
 * משלב metadata, stakeholders, blocks ושדות legacy ל-backward compatibility.
 */
export type VisitReportDocument = {
  id: string;
  project_id: string;
  visit_type: string;
  visit_date: string;
  visit_type_label_he?: string | null;
  project_name?: string | null;
  project_metadata?: ProjectMetadata | null;
  stakeholders?: Stakeholder[];
  main_suppliers?: SupplierRow[];
  fixed_text_blocks?: FixedTextBlock[];
  blocks?: ReportBlock[];
  /** שדות header גולמיים - נשמרים לתאימות לאחור. */
  header_fields_raw?: Record<string, unknown>;
  /** שורות legacy - עד מיגרציה מלאה ל-blocks. */
  lines?: FindingRow[];
  catalog_version?: string | null;
  status?: string | null;
  organization_profile_snapshot?: Record<string, unknown> | null;
};
