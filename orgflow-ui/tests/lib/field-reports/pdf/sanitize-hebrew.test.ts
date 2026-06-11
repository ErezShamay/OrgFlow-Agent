import { describe, expect, it } from "vitest";

import { sanitizePdfHebrewText } from "@/lib/field-reports/pdf/sanitize-hebrew";

describe("sanitizePdfHebrewText", () => {
  it("replaces punctuation that may render as tofu in pdfmake", () => {
    expect(sanitizePdfHebrewText("א - ב")).toBe("א - ב");
    expect(sanitizePdfHebrewText('עו״ד ב״כ דיירים')).toBe(
      'עו"ד ב"כ דיירים'
    );
    expect(sanitizePdfHebrewText("טקסט…")).toBe("טקסט...");
  });
});
