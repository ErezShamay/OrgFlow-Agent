import { describe, expect, it } from "vitest";

import {
  buildConstructionProgressTableBody,
  buildFindingsTableBody,
  buildFindingsTableColumns,
  buildPdfFilename,
  buildVisitReportDocDefinition,
  formatHeaderContact,
  resolveConstructionProgressRows,
  resolveStringList,
  resolveWinterRecommendationsText,
} from "@/lib/field-reports/pdf/build-doc-definition";
import { DEFAULT_WINTER_RECOMMENDATIONS_HE } from "@/lib/field-reports/pdf-block-defaults";

describe("buildFindingsTableColumns", () => {
  it("adds standard and severity columns when catalog lines exist", () => {
    expect(
      buildFindingsTableColumns([
        { id: "1", sort_order: 0, issue_id: "STR-02-001" },
        { id: "2", sort_order: 1 },
      ])
    ).toEqual(["מיקום", "מלאכה", "סטטוס / הערות", "תיאור", "תקן", "חומרה"]);
  });

  it("omits standard columns for free-text-only reports", () => {
    expect(
      buildFindingsTableColumns([{ id: "1", sort_order: 0 }])
    ).toEqual(["מיקום", "מלאכה", "סטטוס / הערות", "תיאור"]);
  });

  it("adds issue marker column when registry markers exist", () => {
    const markers = new Map<string, string>([["line-1", "חדש"]]);

    expect(
      buildFindingsTableColumns([{ id: "1", sort_order: 0 }], markers)
    ).toEqual([
      "מיקום",
      "מלאכה",
      "סטטוס / הערות",
      "תיאור",
      "סטטוס ליקוי",
    ]);
  });
});

describe("buildFindingsTableBody", () => {
  it("maps catalog standard only for issue rows", () => {
    const columns = [
      "מיקום",
      "מלאכה",
      "סטטוס / הערות",
      "תיאור",
      "תקן",
      "חומרה",
    ];
    const body = buildFindingsTableBody(
      [
        {
          id: "1",
          sort_order: 1,
          location: "קומה 3",
          trade: "בטון",
          description: "סדק",
          issue_id: "STR-02-001",
          standard_ref: 'ת"י 466 חלק 1',
          severity: "High",
        },
        {
          id: "2",
          sort_order: 0,
          description: "חופשי",
        },
      ],
      columns
    );

    expect(body[0][3]).toBe("חופשי");
    expect(body[0][4]).toBe("");
    expect(body[1][4]).toBe('ת"י 466 חלק 1');
    expect(body[1][5]).toBe("High");
  });

  it("appends issue marker values when marker column is present", () => {
    const markers = new Map<string, string>([
      ["1", "פתוח מביקור קודם"],
      ["2", "נסגר"],
    ]);
    const columns = [
      "מיקום",
      "מלאכה",
      "סטטוס / הערות",
      "תיאור",
      "סטטוס ליקוי",
    ];
    const body = buildFindingsTableBody(
      [
        { id: "1", sort_order: 0, description: "א" },
        { id: "2", sort_order: 1, description: "ב" },
      ],
      columns,
      markers
    );

    expect(body[0][4]).toBe("פתוח מביקור קודם");
    expect(body[1][4]).toBe("נסגר");
  });
});

describe("formatHeaderContact", () => {
  it("joins phone, address and tagline", () => {
    expect(
      formatHeaderContact({
        report_phone: "03-1234567",
        report_address_line: "רחוב 1",
        report_city: "תל אביב",
        report_tagline: "פיקוח הנדסי",
      })
    ).toBe("03-1234567  |  רחוב 1, תל אביב  |  פיקוח הנדסי");
  });
});

describe("resolveWinterRecommendationsText", () => {
  it("uses custom text when provided", () => {
    expect(
      resolveWinterRecommendationsText({
        winter_recommendations: "טקסט מותאם",
      })
    ).toBe("טקסט מותאם");
  });

  it("falls back to default template when empty", () => {
    expect(resolveWinterRecommendationsText({})).toBe(
      DEFAULT_WINTER_RECOMMENDATIONS_HE
    );
  });
});

describe("resolveStringList", () => {
  it("trims and drops empty list items", () => {
    expect(
      resolveStringList(["  אחד  ", "", "שניים"])
    ).toEqual(["אחד", "שניים"]);
  });
});

describe("resolveConstructionProgressRows", () => {
  it("keeps rows with any filled cell", () => {
    expect(
      resolveConstructionProgressRows({
        construction_progress: [
          { description: "הריסה", status: "בוצע", completion_date: "1.1.26" },
          { description: "", status: "", completion_date: "" },
        ],
      })
    ).toEqual([
      {
        description: "הריסה",
        status: "בוצע",
        completion_date: "1.1.26",
      },
    ]);
  });

  it("returns empty when field is missing", () => {
    expect(resolveConstructionProgressRows({})).toEqual([]);
  });
});

describe("buildConstructionProgressTableBody", () => {
  it("maps rows to PDF table cells", () => {
    expect(
      buildConstructionProgressTableBody([
        {
          description: "ביסוס",
          status: "בתהליך",
          completion_date: "",
        },
      ])
    ).toEqual([["ביסוס", "בתהליך", ""]]);
  });
});

describe("buildVisitReportDocDefinition", () => {
  it("includes construction progress table before findings", () => {
    const definition = buildVisitReportDocDefinition({
      report: {
        id: "r1",
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד / אתר",
        visit_date: "2026-06-01",
        project_name: "בדיקה",
        header_fields: {
          construction_progress: [
            {
              description: "הריסת המבנה",
              status: "בוצע",
              completion_date: "18.11.25",
            },
          ],
        },
        lines: [],
      },
      inspector: { full_name: "ישראל ישראלי" },
    });

    const texts = collectContentTexts(definition.content);
    expect(texts).toContain("סטטוס בניה-שלד");
    expect(collectTableCellTexts(definition.content)).toEqual(
      expect.arrayContaining([
        "תיאור עבודה",
        "הריסת המבנה",
        "18.11.25",
      ])
    );

    const findingsIndex = texts.indexOf("ממצאים / עבודות");
    const progressIndex = texts.indexOf("סטטוס בניה-שלד");
    expect(progressIndex).toBeGreaterThan(-1);
    expect(findingsIndex).toBeGreaterThan(progressIndex);
  });

  it("includes fixed PDF blocks before signature", () => {
    const definition = buildVisitReportDocDefinition({
      report: {
        id: "r1",
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד/אתר",
        visit_date: "2026-06-01",
        project_name: "בדיקה",
        header_fields: {
          project_updates: ["עדכון 1"],
          contractor_notes: ["הערה לקבלן"],
          winter_recommendations: "חורף מותאם",
          inspector_title: "מפקח בכיר",
          inspector_license: "12345",
        },
        lines: [],
      },
      inspector: { full_name: "ישראל ישראלי" },
    });

    const texts = collectContentTexts(definition.content);
    expect(texts).toContain("עדכונים לפרויקט:");
    expect(texts).toContain("עדכון 1");
    expect(texts).toContain("המלצות חורף / עונת גשמים");
    expect(texts).toContain("חורף מותאם");
    expect(texts).toContain("הערות נוספות לקבלן");
    expect(texts.some((text) => text.includes("12345"))).toBe(true);
  });
});

function collectContentTexts(content: unknown): string[] {
  if (!content) {
    return [];
  }

  if (typeof content === "string") {
    return [content];
  }

  if (Array.isArray(content)) {
    return content.flatMap((item) => collectContentTexts(item));
  }

  if (typeof content === "object") {
    const node = content as Record<string, unknown>;
    const texts: string[] = [];

    if (typeof node.text === "string") {
      texts.push(node.text);
    }

    for (const key of ["stack", "ul", "ol", "columns", "content"]) {
      if (key in node) {
        texts.push(...collectContentTexts(node[key]));
      }
    }

    if ("table" in node && node.table && typeof node.table === "object") {
      const table = node.table as { body?: unknown };
      texts.push(...collectContentTexts(table.body));
    }

    return texts;
  }

  return [];
}

function collectTableCellTexts(content: unknown): string[] {
  return collectContentTexts(content);
}

describe("buildPdfFilename", () => {
  it("builds a stable Hebrew filename", () => {
    expect(
      buildPdfFilename({
        id: "r1",
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד/אתר",
        visit_date: "2026-06-01",
        project_name: "פרויקט בדיקה",
        header_fields: {},
        lines: [],
      })
    ).toBe("דוח-מפקח-פרויקט-בדיקה-2026-06-01.pdf");
  });
});
