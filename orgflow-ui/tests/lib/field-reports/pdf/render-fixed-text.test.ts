import { describe, expect, it } from "vitest";

import { buildVisitReportDocDefinition } from "@/lib/field-reports/pdf/build-doc-definition";
import {
  DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE,
  DEFAULT_SAFETY_DISCLAIMER_HE,
} from "@/lib/field-reports/schema/block-defaults";
import { defaultFixedTextBlocks } from "@/lib/field-reports/schema/block-defaults";

function collectTexts(content: unknown): string[] {
  if (!content) {
    return [];
  }
  if (typeof content === "string") {
    return [content];
  }
  if (Array.isArray(content)) {
    return content.flatMap((item) => collectTexts(item));
  }
  if (typeof content === "object") {
    const node = content as Record<string, unknown>;
    const texts: string[] = [];
    if (typeof node.text === "string") {
      texts.push(node.text);
    }
    for (const key of ["stack", "content"]) {
      if (key in node) {
        texts.push(...collectTexts(node[key]));
      }
    }
    return texts;
  }
  return [];
}

describe("renderFixedTextBlocks in PDF", () => {
  it("renders cover disclaimers in header and winter at end", () => {
    const definition = buildVisitReportDocDefinition({
      report: {
        id: "r1",
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד",
        visit_date: "2026-06-01",
        project_name: "בדיקה",
        header_fields: {
          fixed_text_blocks: defaultFixedTextBlocks(),
          include_fixed_text_blocks: true,
          blocks: [],
        },
        lines: [],
      },
      inspector: { full_name: "מפקח" },
    });

    const serialized = JSON.stringify(definition.content);
    expect(serialized).toContain(
      "מלאכות שנמצאה לגביהן אי התאמה/הסתייגות מדווחות בגוף הדו"
    );
    expect(serialized).toContain(DEFAULT_SAFETY_DISCLAIMER_HE.slice(0, 24));
    expect(serialized).toContain("עדכונים לפרויקט:");
    expect(serialized).not.toContain("הסתייגות אי-התאמה");
  });

  it("skips legacy winter section when structured blocks exist", () => {
    const definition = buildVisitReportDocDefinition({
      report: {
        id: "r1",
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד",
        visit_date: "2026-06-01",
        project_name: "בדיקה",
        header_fields: {
          fixed_text_blocks: defaultFixedTextBlocks(),
          include_fixed_text_blocks: true,
          winter_recommendations: "לא אמור להופיע",
        },
        lines: [],
      },
      inspector: { full_name: "מפקח" },
    });

    const texts = collectTexts(definition.content);
    const winterTitleCount = texts.filter(
      (text) => text === "המלצות חורף / עונת גשמים"
    ).length;
    expect(winterTitleCount).toBe(0);
    expect(texts).not.toContain("לא אמור להופיע");
  });

  it("PRD §10 scenario 3 — renders custom section before signature", () => {
    const customBody =
      "הקבלן אחראי לתיקון כל ליקוי שיתגלה במסגרת הביקור.";
    const definition = buildVisitReportDocDefinition({
      report: {
        id: "r-custom-liability",
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד",
        visit_date: "2026-06-01",
        project_name: "בדיקה",
        header_fields: {
          fixed_text_blocks: [
            {
              id: "custom-liability",
              kind: "custom",
              title_he: "הערת אחריות",
              body_he: customBody,
              enabled: true,
              sort_order: 0,
            },
          ],
          include_fixed_text_blocks: true,
          blocks: [],
        },
        lines: [],
      },
      inspector: { full_name: "מפקח" },
    });

    const texts = collectTexts(definition.content);
    const titleIndex = texts.findIndex((text) => text === "הערת אחריות");
    const bodyIndex = texts.findIndex((text) => text === customBody);
    const signatureIndex = texts.findIndex((text) => text === "חתימה");

    expect(titleIndex).toBeGreaterThan(-1);
    expect(bodyIndex).toBeGreaterThan(-1);
    expect(signatureIndex).toBeGreaterThan(-1);
    expect(titleIndex).toBeLessThan(signatureIndex);
    expect(bodyIndex).toBeLessThan(signatureIndex);
  });
});
