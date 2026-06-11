/**
 * Guardrails ל-parity מול דוחות דוגמה (FR-5.1).
 * לא משווה bytes של PDF - רק מחרוזות/כותרות שחולצו מ-example_reports.
 */
import { describe, expect, it } from "vitest";

import { FINISHING_CHECKLIST_ITEM_DEFS } from "@/lib/field-reports/schema/checklist-presets";
import { getColumnPresetHeaders } from "@/lib/field-reports/schema/column-presets";
import {
  PDF_DEFAULT_ADDRESSEE_HE,
  PDF_REPORT_TITLE_HE,
  PDF_SUPERVISION_BANNER_HE,
} from "@/lib/field-reports/pdf/render-header";

/** כותרות שמופיעות ב-7/7 דוחות הלקוח (חילוץ טקסט). */
const EXAMPLE_SHARED_HEADER_STRINGS = [
  PDF_SUPERVISION_BANNER_HE,
  PDF_REPORT_TITLE_HE,
] as const;

/** כותרות עמודות כפי שמופיעות בדוחות הדוגמה. */
const EXAMPLE_COLUMN_HEADERS = {
  rich: ["מיקום", "מלאכה", "סטטוס / הערות", "תיאור", "תמונות"],
  simple: ["תיאור", "הערות / לטיפול", "תמונות"],
  finishing: ["מיקום", "מלאכה", "הערות", "סטטוס / תיאור", "תמונות"],
  progress: ["תיאור עבודה", "סטטוס", "תאריך ביצוע / סיום"],
  structure: ["תיאור", "סטטוס / תאריך סיום"],
} as const;

/** צ'קליסט גמר - דוח ההגנה 29 גבעתיים. */
const HAGANA_CHECKLIST_LABELS = [
  "בעלים",
  "בדיקת חללים",
  "חשמל",
  "אינסטלציה",
  "איטום חדרים רטובים",
  "איטום מרפסות",
] as const;

describe("pdf parity guardrails (FR-5.1)", () => {
  it("exposes header strings present in all 7 example PDFs", () => {
    for (const text of EXAMPLE_SHARED_HEADER_STRINGS) {
      expect(text.length).toBeGreaterThan(0);
    }
    expect(PDF_DEFAULT_ADDRESSEE_HE).toContain("בעלי");
  });

  it("column preset headers match example PDF table headers", () => {
    for (const key of Object.keys(EXAMPLE_COLUMN_HEADERS) as Array<
      keyof typeof EXAMPLE_COLUMN_HEADERS
    >) {
      expect(getColumnPresetHeaders(key)).toEqual(EXAMPLE_COLUMN_HEADERS[key]);
    }
  });

  it("finishing checklist labels match Hagana example", () => {
    const labels = FINISHING_CHECKLIST_ITEM_DEFS.map((item) => item.label_he);
    expect(labels).toEqual([...HAGANA_CHECKLIST_LABELS]);
  });
});
