import type {
  FieldReportDocumentType,
  InspectMode,
  SupervisionReportMeta,
} from "@/lib/field-reports/schema/types";

/** מיפוי UI מהיר → סטטוס פנימי (enum קיים — לא משנים). */
export const QUICK_INSPECT_STATUS_MAP = {
  ok: "OK",
  defect: "DEFECT",
  untouched: "UNCHECKED",
  notApplicable: "NOT_APPLICABLE",
} as const;

type SupervisionMetaSource =
  | SupervisionReportMeta
  | Record<string, unknown>
  | null
  | undefined;

function readDocumentType(source: SupervisionMetaSource): FieldReportDocumentType {
  const raw = source && typeof source === "object" ? source.document_type : null;
  return raw === "handover_protocol" ? "handover_protocol" : "weekly_inspection";
}

function readInspectMode(source: SupervisionMetaSource): InspectMode | null {
  const raw = source && typeof source === "object" ? source.inspect_mode : null;
  return raw === "standard" || raw === "quick" ? raw : null;
}

/** weekly_inspection → quick; handover_protocol → standard; explicit meta wins. */
export function resolveInspectMode(
  source: SupervisionMetaSource
): InspectMode {
  const explicit = readInspectMode(source);
  if (explicit) {
    return explicit;
  }

  return readDocumentType(source) === "weekly_inspection" ? "quick" : "standard";
}

export function defaultInspectModeForDocumentType(
  documentType: FieldReportDocumentType
): InspectMode {
  return documentType === "weekly_inspection" ? "quick" : "standard";
}
