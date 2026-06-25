import type { Content } from "pdfmake/interfaces";

import { catalogFamilyLabelHe } from "@/lib/field-reports/catalog-labels";
import { supervisionVisitLocation } from "@/lib/field-reports/checklist-defect-to-line";
import { MAX_CHECKLIST_ITEM_PHOTOS } from "@/lib/field-reports/checklist-photo-constants";
import { normalizeSupervisionMeta } from "@/lib/field-reports/schema/normalize";
import type {
  ChecklistItemStatus,
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
  SupervisionReportMeta,
} from "@/lib/field-reports/schema/types";
import {
  checklistItemStatusLabelHe,
  groupSupervisionChecklistItems,
} from "@/lib/field-reports/supervision-labels";
import { visibleSupervisionChecklistItems } from "@/lib/field-reports/schema/checklist-item-mutations";
import { constructionStageLabelHe } from "@/lib/field-reports/supervision-stage-labels";
import { formatPdfVisitDateHe } from "./render-page-banner";
import {
  buildRtlTableBodyFromCells,
  pdfTableCell,
  pdfText,
  type PdfTableCell,
} from "./pdf-styles";
import type { ChecklistPhotoData } from "./types";

/** גודל thumbnail לתמונות פריט צ'קליסט (§14.1). */
const CHECKLIST_PHOTO_THUMB_SIZE = 40;

/** צבעי סטטוס ב-PDF (§14.3). */
export const CHECKLIST_STATUS_PDF_COLORS: Record<ChecklistItemStatus, string> = {
  OK: "#16a34a",
  DEFECT: "#dc2626",
  NOT_APPLICABLE: "#6b7280",
  UNCHECKED: "#ea580c",
};

export type ChecklistPhotoLookup = ReadonlyMap<string, readonly string[]>;

export type SupervisionChecklistPdfContext = {
  projectName?: string | null;
  visitDate?: string | null;
  supervisionMeta?: SupervisionReportMeta | null;
  headerFields?: Record<string, unknown>;
};

export type RenderSupervisionChecklistOptions = SupervisionChecklistPdfContext & {
  checklistPhotos?: ChecklistPhotoData[];
};

export type SupervisionChecklistSummary = {
  defect_count: number;
  unchecked_count: number;
  unchecked_with_note_count: number;
  unchecked_without_note_count: number;
};

export function buildChecklistPhotoLookup(
  checklistPhotos: ChecklistPhotoData[] = []
): ChecklistPhotoLookup {
  const lookup = new Map<string, string[]>();

  for (const photo of checklistPhotos) {
    if (!photo.checklistItemId || !photo.dataUrl) {
      continue;
    }
    const existing = lookup.get(photo.checklistItemId) ?? [];
    lookup.set(photo.checklistItemId, [...existing, photo.dataUrl]);
  }

  return lookup;
}

export function summarizeSupervisionChecklistItems(
  items: SupervisionChecklistItem[]
): SupervisionChecklistSummary {
  let defect_count = 0;
  let unchecked_count = 0;
  let unchecked_with_note_count = 0;

  for (const item of items) {
    if (item.status === "DEFECT") {
      defect_count += 1;
    }
    if (item.status === "UNCHECKED") {
      unchecked_count += 1;
      if (item.notes?.trim()) {
        unchecked_with_note_count += 1;
      }
    }
  }

  return {
    defect_count,
    unchecked_count,
    unchecked_with_note_count,
    unchecked_without_note_count:
      unchecked_count - unchecked_with_note_count,
  };
}

export function resolveSupervisionChecklistMeta(
  block: SupervisionChecklistBlock,
  options: SupervisionChecklistPdfContext
): SupervisionReportMeta {
  const fromHeader = options.supervisionMeta
    ?? (options.headerFields
      ? normalizeSupervisionMeta(options.headerFields)
      : null);

  if (fromHeader) {
    return fromHeader;
  }

  return {
    construction_stage: block.construction_stage,
    visit_scope: block.visit_scope,
    apartment_id: block.apartment_id ?? null,
    apartment_number: block.apartment_number ?? null,
    ad_hoc_apartment: block.ad_hoc_apartment ?? false,
    public_area_id: block.public_area_id ?? null,
    public_area_label_he: null,
  };
}

export function buildSupervisionChecklistContextLine(
  block: SupervisionChecklistBlock,
  options: SupervisionChecklistPdfContext
): string {
  const meta = resolveSupervisionChecklistMeta(block, options);
  const parts = [
    options.projectName?.trim() || null,
    options.visitDate ? formatPdfVisitDateHe(options.visitDate) : null,
    constructionStageLabelHe(meta.construction_stage),
    supervisionVisitLocation(meta),
  ].filter(Boolean);

  return parts.join(" · ");
}

export function renderSupervisionChecklist(
  block: SupervisionChecklistBlock,
  options: RenderSupervisionChecklistOptions = {}
): Content[] {
  const visibleItems = visibleSupervisionChecklistItems(block.items);
  if (!visibleItems.length) {
    return [];
  }

  const visibleBlock: SupervisionChecklistBlock = {
    ...block,
    items: visibleItems,
  };

  const photoLookup = buildChecklistPhotoLookup(options.checklistPhotos);
  const groups = groupSupervisionChecklistItems(visibleBlock, (topFamily) =>
    catalogFamilyLabelHe(topFamily)
  );
  const summary = summarizeSupervisionChecklistItems(visibleItems);
  const contextLine = buildSupervisionChecklistContextLine(visibleBlock, options);

  const content: Content[] = [
    pdfText(visibleBlock.title_he, {
      style: "sectionTitle",
      margin: [0, 12, 0, 4],
    }),
  ];

  if (contextLine) {
    content.push(
      pdfText(contextLine, {
        fontSize: 10,
        bold: true,
        alignment: "center",
        margin: [0, 0, 0, 8],
      })
    );
  }

  for (const group of groups) {
    content.push(
      pdfText(group.top_family_label_he, {
        bold: true,
        fontSize: 11,
        margin: [0, 8, 0, 4],
      })
    );

    for (const category of group.categories) {
      content.push(
        pdfText(category.category_name_he, {
          bold: true,
          fontSize: 10,
          margin: [0, 4, 0, 4],
        })
      );

      const headers = ["פריט", "תקן", "סטטוס", "הערות", "תמונות"];
      const body = category.items.map((item) =>
        supervisionItemToCells(item, photoLookup)
      );

      content.push({
        table: {
          headerRows: 1,
          widths: ["*", "auto", "auto", "*", CHECKLIST_PHOTO_THUMB_SIZE * 3 + 12],
          body: buildRtlTableBodyFromCells(headers, body),
        },
        layout: "lightHorizontalLines",
        margin: [0, 0, 0, 8],
      });
    }
  }

  content.push(
    pdfText("סיכום צ'קליסט", {
      style: "sectionTitle",
      margin: [0, 8, 0, 4],
    })
  );
  content.push(
    pdfText(
      [
        `ליקויים: ${summary.defect_count}`,
        `לא נבדק: ${summary.unchecked_count}`,
        summary.unchecked_with_note_count
          ? `(${summary.unchecked_with_note_count} עם הערה)`
          : null,
        summary.unchecked_without_note_count
          ? `(${summary.unchecked_without_note_count} ללא הערה)`
          : null,
      ]
        .filter(Boolean)
        .join(" · "),
      { margin: [0, 0, 0, 12] }
    )
  );

  return content;
}

function supervisionItemToCells(
  item: SupervisionChecklistItem,
  photoLookup: ChecklistPhotoLookup
): PdfTableCell[] {
  return [
    pdfTableCell(item.issue_name_he),
    pdfTableCell(item.standard_ref || ""),
    renderChecklistStatusCell(item),
    pdfTableCell(item.notes?.trim() || ""),
    renderChecklistPhotoCell(item, photoLookup),
  ];
}

function renderChecklistStatusCell(
  item: SupervisionChecklistItem
): PdfTableCell {
  const label = checklistItemStatusLabelHe(item.status);
  const text =
    item.status === "UNCHECKED" && item.notes?.trim()
      ? `${label} — ${item.notes.trim()}`
      : label;

  return {
    text,
    style: "tableCell",
    color: CHECKLIST_STATUS_PDF_COLORS[item.status],
    bold: item.status === "DEFECT",
  };
}

function renderChecklistPhotoCell(
  item: SupervisionChecklistItem,
  photoLookup: ChecklistPhotoLookup
): PdfTableCell {
  const dataUrls = photoLookup
    .get(item.id)
    ?.slice(0, MAX_CHECKLIST_ITEM_PHOTOS);

  if (!dataUrls?.length) {
    return "";
  }

  return {
    columns: dataUrls.map((dataUrl) => ({
      width: CHECKLIST_PHOTO_THUMB_SIZE,
      stack: [
        {
          image: dataUrl,
          width: CHECKLIST_PHOTO_THUMB_SIZE,
          height: CHECKLIST_PHOTO_THUMB_SIZE,
          alignment: "center",
        },
      ],
    })),
    columnGap: 4,
    alignment: "center",
    margin: [0, 2, 0, 2],
  } as PdfTableCell;
}
