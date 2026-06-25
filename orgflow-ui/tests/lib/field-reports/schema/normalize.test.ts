import { describe, expect, it } from "vitest";

import {
  migrateLegacyStakeholdersFromHeader,
  normalizeReportBlocks,
  normalizeStakeholders,
  normalizeVisitReportDocument,
} from "@/lib/field-reports/schema";

describe("migrateLegacyStakeholdersFromHeader", () => {
  it("maps legacy header fields to stakeholder roles", () => {
    expect(
      migrateLegacyStakeholdersFromHeader({
        developer_name: "יזם בע\"מ",
        developer_pm_name: "דני כהן",
        contractor_name: "קבלן א'",
        lawyer_name: "עו\"ד לוי",
        accompanying_lawyer: "עו\"ד שמעון",
      })
    ).toEqual([
      { id: "legacy-developer", role: "developer", name: "יזם בע\"מ" },
      { id: "legacy-project_manager", role: "project_manager", name: "דני כהן" },
      { id: "legacy-contractor", role: "contractor", name: "קבלן א'" },
      { id: "legacy-lawyer_tenants", role: "lawyer_tenants", name: "עו\"ד לוי" },
      {
        id: "legacy-lawyer_accompanying",
        role: "lawyer_accompanying",
        name: "עו\"ד שמעון",
      },
    ]);
  });
});

describe("normalizeStakeholders", () => {
  it("prefers explicit stakeholders over legacy fields with same role", () => {
    expect(
      normalizeStakeholders({
        developer_name: "legacy name",
        stakeholders: [
          {
            id: "dev-1",
            role: "developer",
            name: "explicit name",
          },
        ],
      })
    ).toEqual([
      { id: "dev-1", role: "developer", name: "explicit name", label_he: null },
    ]);
  });

  it("drops sentinel placeholder names from stakeholders", () => {
    expect(
      normalizeStakeholders({
        stakeholders: [
          {
            id: "dev-1",
            role: "developer",
            name: "לא צוין",
          },
        ],
      })
    ).toEqual([]);

    expect(
      migrateLegacyStakeholdersFromHeader({
        developer_name: "לא מצוין",
      })
    ).toEqual([]);
  });
});

describe("normalizeReportBlocks", () => {
  it("converts construction_progress to progress_table block", () => {
    const blocks = normalizeReportBlocks(
      {
        construction_progress: [
          {
            description: "הריסת המבנה",
            status: "בוצע",
            completion_date: "18.11.25",
          },
        ],
      },
      "STRUCTURE_SITE"
    );

    expect(blocks).toHaveLength(1);
    expect(blocks[0]).toMatchObject({
      kind: "progress_table",
      title_he: "סטטוס בניה-שלד",
      column_preset: "progress",
      rows: [
        {
          description: "הריסת המבנה",
          status: "בוצע",
          completion_date: "18.11.25",
        },
      ],
    });
  });

  it("converts report lines to findings_table block", () => {
    const blocks = normalizeReportBlocks({}, "STRUCTURE_SITE", [
      {
        id: "line-1",
        sort_order: 0,
        location: "קומה 3",
        description: "סדק",
      },
    ]);

    expect(blocks).toHaveLength(1);
    expect(blocks[0]).toMatchObject({
      kind: "findings_table",
      title_he: "ממצאים / עבודות",
      column_preset: "simple",
      rows: [
        {
          id: "line-1",
          location: "קומה 3",
          description: "סדק",
        },
      ],
    });
  });
});

describe("normalizeVisitReportDocument", () => {
  it("normalizes legacy report with header_fields and lines without error", () => {
    const document = normalizeVisitReportDocument({
      id: "report-1",
      project_id: "project-1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-01",
      visit_type_label_he: "שלד / אתר",
      project_name: "פרויקט בדיקה",
      header_fields: {
        site_address: "רחוב 1, תל אביב",
        developer_name: "יזם בע\"מ",
        lawyer_name: "עו\"ד לוי",
        construction_progress: [
          {
            description: "ביסוס",
            status: "בתהליך",
            completion_date: "",
          },
        ],
        winter_recommendations: "המלצות חורף",
      },
      lines: [
        {
          id: "line-1",
          sort_order: 0,
          description: "ממצא חופשי",
        },
      ],
    });

    expect(document.id).toBe("report-1");
    expect(document.project_metadata?.site_address).toBe("רחוב 1, תל אביב");
    expect(document.stakeholders).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ role: "developer", name: "יזם בע\"מ" }),
        expect.objectContaining({ role: "lawyer_tenants", name: "עו\"ד לוי" }),
      ])
    );
    expect(document.blocks).toHaveLength(2);
    expect(document.lines).toHaveLength(1);
    expect(document.header_fields_raw).toMatchObject({
      developer_name: "יזם בע\"מ",
      site_address: "רחוב 1, תל אביב",
    });
    expect(document.fixed_text_blocks?.some((block) => block.kind === "winter_recommendations")).toBe(
      true
    );
  });

  it("preserves raw legacy fields even when new structures are derived", () => {
    const headerFields = {
      developer_name: "יזם",
      contractor_name: "קבלן",
    };

    const document = normalizeVisitReportDocument({
      id: "report-2",
      visit_type: "FINISHING_APARTMENTS",
      visit_date: "2026-06-01",
      header_fields: headerFields,
      lines: [],
    });

    expect(document.header_fields_raw).toEqual(headerFields);
    expect(document.stakeholders).toHaveLength(2);
  });
});
