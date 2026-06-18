import "fake-indexeddb/auto";

import { describe, expect, it } from "vitest";

import {
  applySupervisionDefectLinesToReport,
  buildDefectFindingLine,
  supervisionVisitGroupKey,
  supervisionVisitLocation,
} from "@/lib/field-reports/checklist-defect-to-line";
import type {
  SupervisionChecklistBlock,
  SupervisionChecklistItem,
} from "@/lib/field-reports/schema/types";
import type { LocalVisitReportRecord } from "@/lib/field-reports/repositories/reports-repository";

function supervisionBlockFromHeader(
  headerFields: Record<string, unknown>
): SupervisionChecklistBlock | null {
  const blocks = headerFields.blocks;
  if (!Array.isArray(blocks) || !blocks[0] || typeof blocks[0] !== "object") {
    return null;
  }

  return blocks[0] as SupervisionChecklistBlock;
}

const checklistItem: SupervisionChecklistItem = {
  id: "checklist-SUP-FIN-004",
  catalog_issue_id: "SUP-FIN-004",
  issue_name_he: "פוגות לא מלאות",
  category_id: "TILING",
  category_name_he: "ריצוף וחיפוי",
  top_family: "FINISHING_WORKS",
  standard_ref: 'ת"י 1555',
  severity: "Medium",
  status: "DEFECT",
  notes: "בפינה",
  photo_ids: ["primary"],
  linked_line_id: null,
  sort_order: 0,
};

const baseSupervisionBlock: SupervisionChecklistBlock = {
  id: "checklist-main",
  kind: "supervision_checklist",
  title_he: "ביקור דירה 12",
  construction_stage: "FINISHING",
  visit_scope: "APARTMENT",
  apartment_number: "12",
  items: [checklistItem],
  sort_order: 0,
};

const baseRecord: LocalVisitReportRecord = {
  client_report_uuid: "report-1",
  organization_id: "org-1",
  project_id: "proj-1",
  visit_type: "FINISHING_APARTMENTS",
  visit_date: "2026-06-14",
  header_fields: {
    supervision_meta: {
      construction_stage: "FINISHING",
      visit_scope: "APARTMENT",
      apartment_number: "12",
    },
    blocks: [baseSupervisionBlock],
  },
  lines: [],
  local_status: "LOCAL_IN_PROGRESS",
  sync_status: "pending",
  created_at: "2026-06-14T10:00:00.000Z",
  updated_at: "2026-06-14T10:00:00.000Z",
};

describe("buildDefectFindingLine (§9.1)", () => {
  it("maps apartment visit location and group_key", () => {
    const line = buildDefectFindingLine({
      item: checklistItem,
      block: baseSupervisionBlock,
      meta: {
        construction_stage: "FINISHING",
        visit_scope: "APARTMENT",
        apartment_number: "12",
      },
    });

    expect(line.issue_id).toBe("SUP-FIN-004");
    expect(line.description).toBe("פוגות לא מלאות");
    expect(line.location).toBe("דירה 12");
    expect(line.group_key).toBe("apartment:12");
    expect(line.photo_ids).toEqual(["primary"]);
    expect(line.block_id).toBe("checklist-main");
  });

  it("maps public area visit location", () => {
    expect(
      supervisionVisitLocation({
        construction_stage: "FINISHING",
        visit_scope: "PUBLIC_AREA",
        public_area_id: "LOBBY",
        public_area_label_he: "לובי / כניסה",
      })
    ).toBe("לובי / כניסה");

    expect(
      supervisionVisitGroupKey({
        construction_stage: "FINISHING",
        visit_scope: "PUBLIC_AREA",
        public_area_id: "LOBBY",
      })
    ).toBe("area:LOBBY");
  });
});

describe("applySupervisionDefectLinesToReport", () => {
  it("creates finding line and links checklist item", () => {
    const synced = applySupervisionDefectLinesToReport(baseRecord);

    expect(synced.lines).toHaveLength(1);
    expect(synced.lines[0]?.issue_id).toBe("SUP-FIN-004");
    expect(synced.lines[0]?.has_photo).toBe(true);

    const block = supervisionBlockFromHeader(synced.header_fields);
    expect(block?.items[0]?.linked_line_id).toBeTruthy();
  });

  it("cancels linked line when defect status cleared", () => {
    const withLine = applySupervisionDefectLinesToReport(baseRecord);
    const linkedId = supervisionBlockFromHeader(withLine.header_fields)
      ?.items[0]?.linked_line_id;

    const withLineBlock = supervisionBlockFromHeader(withLine.header_fields);
    const cleared = applySupervisionDefectLinesToReport({
      ...withLine,
      header_fields: {
        ...withLine.header_fields,
        blocks: [
          {
            ...(withLineBlock ?? baseSupervisionBlock),
            items: [
              {
                ...checklistItem,
                status: "OK" as const,
                linked_line_id: linkedId,
              },
            ],
          },
        ],
      },
    });

    expect(cleared.lines[0]?.status).toBe("CANCELLED");
    expect(
      supervisionBlockFromHeader(cleared.header_fields)?.items[0]?.linked_line_id
    ).toBeNull();
  });

  it("creates finding line for DEFECT without photo (L1 instant loop)", () => {
    const synced = applySupervisionDefectLinesToReport({
      ...baseRecord,
      header_fields: {
        ...baseRecord.header_fields,
        blocks: [
          {
            ...baseSupervisionBlock,
            items: [{ ...checklistItem, photo_ids: [], linked_line_id: null }],
          },
        ],
      },
    });

    expect(synced.lines).toHaveLength(1);
    expect(synced.lines[0]?.issue_id).toBe("SUP-FIN-004");
    expect(
      supervisionBlockFromHeader(synced.header_fields)?.items[0]?.linked_line_id
    ).toBeTruthy();
  });
});
