import { createClientLineUuid } from "@/lib/field-reports/ids";
import {
  normalizeHeaderFields,
  patchHeaderFieldsBlocks,
  serializeHeaderFieldsForApi,
} from "@/lib/field-reports/header-fields";
import { normalizeSupervisionMeta } from "@/lib/field-reports/schema/normalize";
import type {
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
  SupervisionReportMeta,
} from "@/lib/field-reports/schema/types";
import type {
  LocalVisitReportLine,
  LocalVisitReportRecord,
  UpsertLineInput,
} from "@/lib/field-reports/repositories/reports-repository";
import { isSupervisionChecklistReport } from "@/lib/field-reports/supervision-checklist-builder";
import { formatVisitedApartmentsSummaryHe } from "@/lib/field-reports/visited-apartments-summary";

const CHECKLIST_CANCELLED_NOTE = "[מבוטל — עודכן בצ'קליסט]";

export function supervisionVisitLocation(meta: SupervisionReportMeta): string {
  if (meta.visit_scope === "MULTI_APARTMENT") {
    const summary = formatVisitedApartmentsSummaryHe(
      meta.visited_apartments ?? []
    );
    return summary || "מספר דירות";
  }

  if (meta.visit_scope === "WHOLE_BUILDING") {
    return "כלל הבניין";
  }

  if (meta.visit_scope === "APARTMENT") {
    const number = meta.apartment_number?.trim();
    return number ? `דירה ${number}` : "דירה";
  }

  return meta.public_area_label_he?.trim() || "שטחים ציבוריים";
}

export function supervisionVisitGroupKey(meta: SupervisionReportMeta): string {
  if (meta.visit_scope === "WHOLE_BUILDING") {
    return "building:whole";
  }

  if (meta.visit_scope === "MULTI_APARTMENT") {
    const number = meta.apartment_number?.trim();
    if (number) {
      return `apartment:${number}`;
    }
    return "apartment:multi";
  }

  if (meta.visit_scope === "APARTMENT") {
    const number = meta.apartment_number?.trim() || "unknown";
    return `apartment:${number}`;
  }

  return `area:${meta.public_area_id ?? "unknown"}`;
}

/** מטא לבלוק צ'קליסט — דירה בודדת בתוך דוח מרובה דירות. */
export function supervisionMetaForChecklistBlock(
  reportMeta: SupervisionReportMeta,
  block: SupervisionChecklistBlock
): SupervisionReportMeta {
  if (block.apartment_number?.trim()) {
    return {
      ...reportMeta,
      visit_scope: "APARTMENT",
      apartment_id: block.apartment_id ?? null,
      apartment_number: block.apartment_number,
      owner_name: null,
      ad_hoc_apartment: block.ad_hoc_apartment ?? false,
    };
  }

  return reportMeta;
}

/** מיפוי DEFECT + תמונה → שורת ממצא (§9.1). */
export function buildDefectFindingLine(params: {
  item: SupervisionChecklistItem;
  block: SupervisionChecklistBlock;
  meta: SupervisionReportMeta;
  existingLine?: LocalVisitReportLine | null;
}): UpsertLineInput {
  const { item, block, meta, existingLine } = params;
  const location = supervisionVisitLocation(meta);

  return {
    client_line_uuid: existingLine?.client_line_uuid,
    id: existingLine?.id,
    server_line_id: existingLine?.server_line_id ?? null,
    sort_order: existingLine?.sort_order,
    issue_id: item.catalog_issue_id,
    description: item.issue_name_he,
    standard_ref: item.standard_ref,
    trade: item.category_name_he,
    severity: item.severity ?? null,
    location,
    group_key: supervisionVisitGroupKey(meta),
    group_label_he: location,
    block_id: block.id,
    photo_ids: [...item.photo_ids],
    has_photo: item.photo_ids.length > 0,
    status: "NEEDS_ACTION",
    notes: item.notes ?? existingLine?.notes ?? null,
  };
}

function findLineByLinkedId(
  lines: LocalVisitReportLine[],
  linkedLineId: string | null | undefined
): LocalVisitReportLine | null {
  if (!linkedLineId) {
    return null;
  }

  return (
    lines.find(
      (line) =>
        line.client_line_uuid === linkedLineId || line.id === linkedLineId
    ) ?? null
  );
}

function cancelLinkedFindingLine(
  line: LocalVisitReportLine
): LocalVisitReportLine {
  const notes = line.notes?.trim();
  const alreadyCancelled = notes?.includes(CHECKLIST_CANCELLED_NOTE);

  return {
    ...line,
    status: "CANCELLED",
    notes: alreadyCancelled
      ? notes
      : [notes, CHECKLIST_CANCELLED_NOTE].filter(Boolean).join(" "),
  };
}

/** יוצר/מעדכן שורות ממצא ל-DEFECT ומבטל קישורים שהוסרו (§9.1–§9.2). */
export function applySupervisionDefectLinesToReport(
  record: LocalVisitReportRecord
): LocalVisitReportRecord {
  const normalizedHeader = normalizeHeaderFields(
    record.header_fields,
    record.visit_type
  );

  if (!isSupervisionChecklistReport(normalizedHeader.blocks)) {
    return record;
  }

  const checklistBlocks = normalizedHeader.blocks.filter(
    (entry): entry is SupervisionChecklistBlock =>
      entry.kind === "supervision_checklist"
  );

  if (!checklistBlocks.length) {
    return record;
  }

  const reportMeta = normalizeSupervisionMeta(record.header_fields);
  if (!reportMeta) {
    return record;
  }

  let lines = [...record.lines];
  const updatedBlocks = normalizedHeader.blocks.map((entry) => {
    if (entry.kind !== "supervision_checklist") {
      return entry;
    }

    const blockMeta = supervisionMetaForChecklistBlock(reportMeta, entry);
    const { updatedBlock, lines: nextLines } = applyDefectLinesForChecklistBlock(
      entry,
      blockMeta,
      lines
    );
    lines = nextLines;
    return updatedBlock;
  });

  const patchedHeader = patchHeaderFieldsBlocks(
    normalizedHeader,
    updatedBlocks,
    record.visit_type
  );

  const header_fields = serializeHeaderFieldsForApi(patchedHeader);
  const supervisionMeta = record.header_fields?.supervision_meta;
  if (supervisionMeta && typeof supervisionMeta === "object") {
    header_fields.supervision_meta = supervisionMeta;
  }

  return {
    ...record,
    lines,
    header_fields,
  };
}

function applyDefectLinesForChecklistBlock(
  block: SupervisionChecklistBlock,
  meta: SupervisionReportMeta,
  lines: LocalVisitReportLine[]
): {
  updatedBlock: SupervisionChecklistBlock;
  lines: LocalVisitReportLine[];
} {
  let nextLines = [...lines];
  const updatedItems = block.items.map((item) => {
    const existingLine = findLineByLinkedId(nextLines, item.linked_line_id);

    if (item.status === "DEFECT") {
      const payload = buildDefectFindingLine({
        item,
        block,
        meta,
        existingLine,
      });

      if (existingLine) {
        nextLines = nextLines.map((line) =>
          line.client_line_uuid === existingLine.client_line_uuid
            ? {
                ...line,
                ...payload,
                client_line_uuid: line.client_line_uuid,
                id: line.id,
              }
            : line
        );
        return item;
      }

      const clientLineUuid = createClientLineUuid();
      const newLine: LocalVisitReportLine = {
        id: clientLineUuid,
        client_line_uuid: clientLineUuid,
        server_line_id: null,
        sort_order: nextLines.length + 1,
        location: payload.location ?? null,
        trade: payload.trade ?? null,
        status: payload.status ?? null,
        description: payload.description ?? null,
        notes: payload.notes ?? null,
        severity: payload.severity ?? null,
        standard_ref: payload.standard_ref ?? null,
        catalog_reference_id: null,
        issue_id: payload.issue_id ?? null,
        group_key: payload.group_key ?? null,
        group_label_he: payload.group_label_he ?? null,
        block_id: payload.block_id ?? null,
        linked_issue_id: null,
        has_photo: payload.has_photo,
        photo_ids: payload.photo_ids,
      };

      nextLines.push(newLine);

      return {
        ...item,
        linked_line_id: clientLineUuid,
      };
    }

    if (existingLine) {
      nextLines = nextLines.map((line) =>
        line.client_line_uuid === existingLine.client_line_uuid
          ? cancelLinkedFindingLine(line)
          : line
      );

      return {
        ...item,
        linked_line_id: null,
      };
    }

    return item;
  });

  return {
    updatedBlock: {
      ...block,
      items: updatedItems,
    },
    lines: nextLines,
  };
}
