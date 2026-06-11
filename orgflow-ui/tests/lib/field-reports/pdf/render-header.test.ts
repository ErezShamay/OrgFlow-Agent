import { describe, expect, it } from "vitest";

import { buildCoverNumberedEntries } from "@/lib/field-reports/pdf/render-header-boilerplate";
import {
  PDF_DEFAULT_ADDRESSEE_HE,
  PDF_REPORT_TITLE_HE,
  PDF_SUPERVISION_BANNER_HE,
  renderVisitReportHeader,
} from "@/lib/field-reports/pdf/render-header";

describe("renderVisitReportHeader", () => {
  it("renders client-style titles, scheme, addressee and project dates", () => {
    const content = renderVisitReportHeader({
      report: {
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד / אתר",
        visit_date: "2026-06-01",
        project_name: "פרויקט אורנים",
        header_fields: {
          scheme: "TAMA38_STRENGTHENING",
          scheme_label_he:
            'התחדשות עירונית - פרויקט חיזוק תמ"א',
          project_start_date: "2024-01-01",
          project_end_date: "2027-12-31",
          housing_units_count: 42,
          developer_name: "יזם בע״מ",
          lawyer_name: "עו״ד כהן",
          site_address: "רחוב הרצל 1",
          project_updates: ["עדכון לפרויקט"],
          fixed_text_blocks: [],
          include_fixed_text_blocks: true,
        },
      },
    });

    const texts = collectContentTexts(content);
    expect(texts).not.toContain(PDF_SUPERVISION_BANNER_HE);
    expect(texts).toContain(PDF_REPORT_TITLE_HE);
    expect(texts).toContain('התחדשות עירונית - פרויקט חיזוק תמ"א');
    expect(texts).toContain(`לכבוד: ${PDF_DEFAULT_ADDRESSEE_HE}`);
    expect(texts).toContain("תאריך התחלת הפרויקט: 01.01.2024");
    expect(texts).toContain("תאריך ביקור באתר: 01.06.2026");
    expect(texts).toContain('בפרויקט ייבנו סה"כ 42 יחידות דיור');
    expect(texts).toContain('שם החברה היזמית: יזם בע"מ');
    expect(texts).toContain('עו"ד ב"כ הדיירים: עו"ד כהן');
    expect(texts).toContain("כתובת אתר: רחוב הרצל 1");
    expect(texts).toContain("עדכונים לפרויקט:");
    expect(texts).toContain("עדכון לפרויקט");

    const coverEntries = buildCoverNumberedEntries(
      {
        project_updates: ["עדכון לפרויקט"],
        fixed_text_blocks: [],
        include_fixed_text_blocks: true,
      },
      "2026-06-01"
    );
    expect(coverEntries.length).toBeGreaterThanOrEqual(3);
    expect(JSON.stringify(content)).toContain(
      "מלאכות שנמצאה לגביהן אי התאמה"
    );
  });

  it("falls back to legacy header fields when metadata is missing", () => {
    const content = renderVisitReportHeader({
      report: {
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד / אתר",
        visit_date: "2026-06-01",
        project_name: "בדיקה",
        header_fields: {
          developer_name: "Legacy Dev",
          developer_pm_name: "Legacy PM",
          lawyer_name: "Legacy Lawyer",
          site_address: "Legacy Site",
        },
      },
    });

    const texts = collectContentTexts(content);
    expect(texts).toContain("שם החברה היזמית: Legacy Dev");
    expect(texts).toContain("מנהל הפרויקט מטעם היזם: Legacy PM");
    expect(texts).toContain('עו"ד ב"כ הדיירים: Legacy Lawyer');
    expect(texts).toContain("כתובת אתר: Legacy Site");
    expect(texts).not.toContain("תאריך התחלת פרויקט:");
  });

  it("renders stakeholders from explicit array with role labels", () => {
    const content = renderVisitReportHeader({
      report: {
        visit_type: "FINISHING_APARTMENTS",
        visit_type_label_he: "גמר",
        visit_date: "2026-06-01",
        project_name: "ההגנה",
        header_fields: {
          stakeholders: [
            {
              id: "arch-1",
              role: "architect",
              name: "אדריכלית לוי",
            },
            {
              id: "cont-1",
              role: "contractor",
              name: "קבלן א'",
            },
          ],
          main_suppliers: [
            {
              id: "s1",
              category_he: "מטבחים",
              vendor_name: "איקאה",
            },
          ],
        },
      },
    });

    const texts = collectContentTexts(content);
    expect(texts).toContain("אדריכל הפרויקט: אדריכלית לוי");
    expect(texts).toContain("קבלן מבצע: קבלן א'");
    expect(texts).toContain("ספקים עיקריים לפרויקט:");
    expect(texts).toContain("-איקאה.מטבחים");
  });
});

const PDF_CONTENT_SKIP_KEYS = new Set([
  "margin",
  "width",
  "height",
  "fontSize",
  "alignment",
  "direction",
  "font",
  "style",
  "fillColor",
  "color",
  "pageBreak",
]);

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
    } else if (node.text !== undefined) {
      texts.push(...collectContentTexts(node.text));
    }

    for (const [key, value] of Object.entries(node)) {
      if (key === "text" || PDF_CONTENT_SKIP_KEYS.has(key)) {
        continue;
      }
      texts.push(...collectContentTexts(value));
    }

    return texts;
  }

  return [];
}
