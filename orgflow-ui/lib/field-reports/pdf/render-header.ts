import type { Content } from "pdfmake/interfaces";

import { normalizeHeaderFields } from "../header-fields";
import { buildCoverNumberedEntries } from "./render-header-boilerplate";
import { formatPdfVisitDateHe } from "./render-page-banner";
import { pdfText } from "./pdf-styles";
import { projectSchemeLabelHe } from "../project-scheme-labels";
import { stakeholderRoleLabelHe } from "../stakeholder-role-labels";
import type { ProjectMetadata, Stakeholder, StakeholderRole } from "../schema/types";
import type { OrganizationProfileSnapshot, PdfVisitReport } from "./types";

/** כותרת עליונה כמו בדוחות הלקוח (7/7). */
export const PDF_SUPERVISION_BANNER_HE =
  "פיקוח בניה הנדסי מטעם הדיירים";

/** כותרת דוח ראשית - דוחות דוגמה. */
export const PDF_REPORT_TITLE_HE =
  "דוח מפקח/ת הנדסי מטעם בעלי הדירות";

/** נמען ברירת מחדל כשאין addressee_label_he. */
export const PDF_DEFAULT_ADDRESSEE_HE = "בעלי הקרקע / בעלי הדירות";

/** תוויות stakeholders ב-PDF - גרשיים ישרים לתאימות גופן. */
const PDF_STAKEHOLDER_LABELS_HE: Record<StakeholderRole, string> = {
  developer: "שם החברה היזמית",
  project_manager: "מנהל הפרויקט מטעם היזם",
  site_manager: "מנהל עבודה",
  contractor: "קבלן מבצע",
  lawyer_tenants: 'עו"ד ב"כ הדיירים',
  lawyer_accompanying: 'עו"ד מלווה',
  architect: "אדריכל הפרויקט",
};

export const PDF_DEFAULT_ILLUSTRATION_CAPTION_HE =
  "הדמיית הפרויקט להמחשה בלבד";

/** סדר תצוגת stakeholders בכותרת PDF. */
const STAKEHOLDER_RENDER_ORDER: readonly StakeholderRole[] = [
  "developer",
  "project_manager",
  "site_manager",
  "contractor",
  "lawyer_tenants",
  "lawyer_accompanying",
  "architect",
];

export type RenderVisitReportHeaderInput = {
  report: Pick<
    PdfVisitReport,
    | "visit_type"
    | "visit_type_label_he"
    | "visit_date"
    | "project_name"
    | "header_fields"
  >;
  profile?: OrganizationProfileSnapshot | null;
  logoDataUrl?: string | null;
  illustrationDataUrl?: string | null;
};

export function formatOrgAddress(
  profile: OrganizationProfileSnapshot | null | undefined
): string {
  const parts = [
    profile?.report_address_line,
    profile?.report_city,
  ].filter(Boolean);
  return parts.join(", ");
}

export function formatHeaderContact(
  profile: OrganizationProfileSnapshot | null | undefined
): string {
  return [
    profile?.report_phone,
    formatOrgAddress(profile),
    profile?.report_tagline,
  ]
    .filter(Boolean)
    .join("  |  ");
}

/**
 * מרender את בלוק הכותרת ב-PDF - metadata, stakeholders, עדכוני פרויקט (FR-1.4).
 * גוף הדוח (ממצאים, blocks) נשאר ב-build-doc-definition.
 */
export function renderVisitReportHeader(
  input: RenderVisitReportHeaderInput
): Content[] {
  const { report, profile, logoDataUrl, illustrationDataUrl } = input;
  const headerFields = report.header_fields || {};
  const normalized = normalizeHeaderFields(headerFields, report.visit_type);
  const metadata = normalized.project_metadata;
  const schemeLine = resolveSchemeLabelHe(metadata, headerFields);
  const addressee = resolveAddresseeLabel(metadata, headerFields);
  const coverNumberedEntries = buildCoverNumberedEntries(
    headerFields,
    report.visit_date
  );

  const content: Content[] = [];

  if (logoDataUrl) {
    content.push({
      image: logoDataUrl,
      width: 72,
      alignment: "center",
      margin: [0, 0, 0, 10],
    });
  }

  for (const line of buildCoverMetadataLines(metadata, headerFields, report)) {
    content.push(pdfText(line, { fontSize: 10, margin: [0, 0, 0, 2] }));
  }

  const developerLine = resolveDeveloperDisplayLine(normalized, report);
  if (developerLine) {
    content.push(pdfText(developerLine, { margin: [0, 4, 0, 4] }));
  }

  content.push(
    pdfText(`לכבוד: ${addressee}`, { margin: [0, 0, 0, 6] }),
    pdfText(PDF_REPORT_TITLE_HE, {
      style: "reportTitle",
      alignment: "center",
      margin: [0, 6, 0, 4],
    })
  );

  if (schemeLine) {
    content.push(
      pdfText(schemeLine, {
        style: "subTitle",
        alignment: "center",
        margin: [0, 0, 0, 4],
      })
    );
  }

  content.push(
    pdfText(report.visit_type_label_he, {
      style: "subTitle",
      alignment: "center",
      margin: [0, 0, 0, 10],
    })
  );

  const stakeholderLines = buildStakeholderLines(
    normalized.stakeholders,
    normalized
  );
  content.push(
    pdfText("פרטים כללים:", {
      style: "sectionTitle",
      margin: [0, 0, 0, 4],
    })
  );
  for (const line of stakeholderLines) {
    content.push(pdfText(line, { margin: [0, 0, 0, 2] }));
  }

  const tenantChanges =
    stringField(metadata.tenant_changes_notes) ||
    stringField(headerFields.tenant_changes_notes);
  if (tenantChanges) {
    content.push(pdfText(`שינויי דיירים: ${tenantChanges}`, { margin: [0, 4, 0, 4] }));
  }

  if (coverNumberedEntries.length) {
    content.push(
      pdfText("עדכונים לפרויקט:", {
        style: "sectionTitle",
        margin: [0, 8, 0, 4],
      })
    );
    content.push({
      ol: coverNumberedEntries.map((item) => pdfText(item) as Content),
      margin: [0, 0, 0, 8],
    });
  }

  const supplierLines = buildSupplierLines(normalized.main_suppliers);
  if (supplierLines.length) {
    content.push(
      pdfText("ספקים עיקריים לפרויקט:", {
        style: "sectionTitle",
        margin: [0, 4, 0, 4],
      })
    );
    for (const line of supplierLines) {
      content.push(pdfText(line, { margin: [0, 0, 0, 2] }));
    }
  }

  content.push({ text: "", pageBreak: "before" });
  content.push(
    ...renderProjectIllustrationSection(
      metadata,
      headerFields,
      normalized.stakeholders,
      illustrationDataUrl
    )
  );

  const structureDocSection = renderStructureDocumentationSection(
    metadata,
    headerFields
  );
  if (structureDocSection.length) {
    content.push({ text: "", pageBreak: "before" });
    content.push(...structureDocSection);
  }

  return content;
}

/** @deprecated - השתמשו ב-PDF_DOCUMENT_STYLES מ-pdf-styles (נשמר לתאימות בדיקות). */
export { PDF_DOCUMENT_STYLES as PDF_HEADER_STYLES } from "./pdf-styles";

function buildCoverMetadataLines(
  metadata: ProjectMetadata,
  headerFields: Record<string, unknown>,
  report: Pick<PdfVisitReport, "visit_date" | "project_name">
): string[] {
  const lines: string[] = [];

  const startDate = formatPdfVisitDateHe(
    stringField(metadata.project_start_date) ||
      stringField(headerFields.project_start_date)
  );
  const endDate = formatPdfVisitDateHe(
    stringField(metadata.project_end_date) ||
      stringField(headerFields.project_end_date)
  );
  const graceDate = formatPdfVisitDateHe(
    stringField(metadata.project_grace_end_date) ||
      stringField(headerFields.project_grace_end_date)
  );
  const visitDate = formatPdfVisitDateHe(report.visit_date);

  if (startDate) {
    lines.push(`תאריך התחלת הפרויקט: ${startDate}`);
  }
  if (endDate) {
    lines.push(`תאריך סיום הפרויקט: ${endDate}`);
  }
  if (graceDate) {
    lines.push(`תאריך סיום הפרויקט (גרייס): ${graceDate}`);
  }
  if (visitDate) {
    lines.push(`תאריך ביקור באתר: ${visitDate}`);
  }

  const ganttForecast =
    stringField(metadata.gantt_forecast) ||
    stringField(headerFields.gantt_forecast);
  if (ganttForecast) {
    lines.push(`צפי לוחות זמנים (גנט): ${ganttForecast}`);
  }

  if (report.project_name?.trim()) {
    lines.push(report.project_name.trim());
  }

  return lines;
}

function resolveDeveloperDisplayLine(
  normalized: ReturnType<typeof normalizeHeaderFields>,
  report: Pick<PdfVisitReport, "project_name">
): string {
  const developer = normalized.developer_name.trim();
  if (developer) {
    return developer;
  }
  return report.project_name?.trim() || "";
}

function renderProjectIllustrationSection(
  metadata: ProjectMetadata,
  headerFields: Record<string, unknown>,
  stakeholders: Stakeholder[],
  illustrationDataUrl?: string | null
): Content[] {
  const content: Content[] = [];
  const caption =
    stringField(metadata.illustration_caption_he) ||
    stringField(headerFields.illustration_caption_he) ||
    PDF_DEFAULT_ILLUSTRATION_CAPTION_HE;
  const sourceNote =
    stringField(metadata.illustration_source_he) ||
    stringField(headerFields.illustration_source_he);
  const architect = stakeholders.find((item) => item.role === "architect");
  const architectName =
    architect?.name?.trim() || stringField(metadata.architect_name);
  const housingUnits = metadata.housing_units_count;

  content.push(
    pdfText(caption, {
      style: "sectionTitle",
      alignment: "center",
      margin: [0, 8, 0, 8],
    })
  );

  if (illustrationDataUrl) {
    content.push({
      image: illustrationDataUrl,
      width: 460,
      alignment: "center",
      margin: [0, 0, 0, 8],
    });
  }

  if (sourceNote) {
    content.push(
      pdfText(sourceNote, {
        alignment: "center",
        fontSize: 9,
        margin: [0, 0, 0, 6],
      })
    );
  }

  if (architectName) {
    content.push(
      pdfText(`אדריכל הפרויקט: ${architectName}`, {
        alignment: "center",
        margin: [0, 0, 0, 4],
      })
    );
  }

  if (housingUnits !== null && housingUnits !== undefined) {
    content.push(
      pdfText(`בפרויקט ייבנו סה"כ ${housingUnits} יחידות דיור`, {
        alignment: "center",
        margin: [0, 0, 0, 8],
      })
    );
  }

  return content;
}

function renderStructureDocumentationSection(
  metadata: ProjectMetadata,
  headerFields: Record<string, unknown>
): Content[] {
  const structureDocDate = formatPdfVisitDateHe(
    stringField(metadata.structure_documentation_date) ||
      stringField(headerFields.structure_documentation_date)
  );

  if (!structureDocDate) {
    return [];
  }

  return [
    pdfText(`תיעוד המבנה מיום ${structureDocDate}`, {
      alignment: "center",
      margin: [0, 24, 0, 12],
    }),
  ];
}

function buildStakeholderLines(
  stakeholders: Stakeholder[],
  normalized: ReturnType<typeof normalizeHeaderFields>
): string[] {
  const byRole = new Map(stakeholders.map((item) => [item.role, item]));
  const lines: string[] = [];

  for (const role of STAKEHOLDER_RENDER_ORDER) {
    const stakeholder = byRole.get(role);
    const name = stakeholder?.name?.trim();
    if (!name) {
      continue;
    }
    const label =
      stakeholder?.label_he?.trim()
      || PDF_STAKEHOLDER_LABELS_HE[role]
      || stakeholderRoleLabelHe(role);
    lines.push(`${label}: ${name}`);
  }

  const siteAddress = normalized.site_address.trim();
  if (siteAddress) {
    lines.push(`כתובת אתר: ${siteAddress}`);
  }

  if (lines.length) {
    return lines;
  }

  return buildLegacyStakeholderFallback(normalized);
}

function buildLegacyStakeholderFallback(
  normalized: ReturnType<typeof normalizeHeaderFields>
): string[] {
  const developerPmName =
    normalized.developer_pm_name.trim() || normalized.contractor_name.trim();

  return [
    `יזם: ${displayValue(normalized.developer_name)}`,
    `מנהל פרויקט מטעם יזם: ${displayValue(developerPmName)}`,
    `עו"ד ב"כ הדיירים: ${displayValue(normalized.lawyer_name)}`,
    `עו"ד מלווה: ${displayValue(normalized.accompanying_lawyer)}`,
    `כתובת אתר: ${displayValue(normalized.site_address)}`,
  ];
}

function buildSupplierLines(
  suppliers: ReturnType<typeof normalizeHeaderFields>["main_suppliers"]
): string[] {
  return suppliers
    .map((row) => {
      const category = row.category_he.trim();
      const vendor = row.vendor_name.trim();
      if (!category && !vendor) {
        return "";
      }
      if (category && vendor) {
        return `-${vendor}.${category}`;
      }
      return category || vendor;
    })
    .filter(Boolean);
}

function resolveSchemeLabelHe(
  metadata: ProjectMetadata,
  headerFields: Record<string, unknown>
): string {
  const explicit =
    stringField(metadata.scheme_label_he) ||
    stringField(headerFields.scheme_label_he);
  if (explicit) {
    return explicit;
  }

  const scheme = metadata.scheme ?? headerFields.scheme;
  if (
    scheme === "TAMA38_STRENGTHENING" ||
    scheme === "TAMA38_DEMOLITION_REBUILD" ||
    scheme === "TAMA38_RELOCATED_BUILD"
  ) {
    return projectSchemeLabelHe(scheme);
  }

  return "";
}

function resolveAddresseeLabel(
  metadata: ProjectMetadata,
  headerFields: Record<string, unknown>
): string {
  return (
    stringField(metadata.addressee_label_he) ||
    stringField(headerFields.addressee_label_he) ||
    PDF_DEFAULT_ADDRESSEE_HE
  );
}

export function resolveStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => String(item).trim()).filter(Boolean);
}

function stringField(value: unknown): string {
  if (typeof value === "string") {
    return value.trim();
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value).trim();
}

function parseOptionalNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function displayValue(value: string): string {
  const text = value.trim();
  return text || "-";
}
