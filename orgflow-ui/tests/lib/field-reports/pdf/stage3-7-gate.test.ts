import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  normalizePdfExtractedText,
  pdfExtractContainsPhrase,
} from "./sample-report-parity-helpers";

const UI_ROOT = path.resolve(__dirname, "../../../..");

describe("stage 3.7 gate (sample_reports PDF parity)", () => {
  it("ships sample_reports parity tests and fixtures", () => {
    const files = [
      "tests/lib/field-reports/pdf/sample-reports-parity.test.ts",
      "tests/lib/field-reports/pdf/sample-report-parity-helpers.ts",
      "tests/lib/field-reports/pdf/fixtures/sample-reports-parity.ts",
    ];

    for (const relativePath of files) {
      const source = readFileSync(path.join(UI_ROOT, relativePath), "utf8");
      expect(source.length).toBeGreaterThan(100);
    }
  });

  it("normalizes PDF extraction spacing and quote artifacts", () => {
    const extracted =
      'התחדשות עירונית -פרויקט חיזוק תמ"א פרטים כללים :';
    const expected = 'התחדשות עירונית - פרויקט חיזוק תמ"א';

    expect(pdfExtractContainsPhrase(extracted, expected)).toBe(true);
    expect(normalizePdfExtractedText('תיאור  סטטוס / תאריך  סיום')).toBe(
      "תיאורסטטוס/תאריךסיום"
    );
  });
});
