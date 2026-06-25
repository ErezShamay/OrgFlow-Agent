import { describe, expect, it } from "vitest";

import {
  displayOptionalText,
  normalizeOptionalTextInput,
  optionalTextForSave,
  UNSPECIFIED_FIELD_LABEL_HE,
} from "@/lib/validation/optional-field-display";

describe("optional-field-display", () => {
  it("treats sentinel labels as empty in edit inputs", () => {
    expect(normalizeOptionalTextInput(null)).toBe("");
    expect(normalizeOptionalTextInput("")).toBe("");
    expect(normalizeOptionalTextInput("  ")).toBe("");
    expect(normalizeOptionalTextInput(UNSPECIFIED_FIELD_LABEL_HE)).toBe("");
    expect(normalizeOptionalTextInput("לא מצוין")).toBe("");
    expect(normalizeOptionalTextInput("  יזם לדוגמה  ")).toBe("יזם לדוגמה");
  });

  it("shows sentinel only in read-only display", () => {
    expect(displayOptionalText(null)).toBe(UNSPECIFIED_FIELD_LABEL_HE);
    expect(displayOptionalText("לא מצוין")).toBe(UNSPECIFIED_FIELD_LABEL_HE);
    expect(displayOptionalText("יזם")).toBe("יזם");
  });

  it("does not persist sentinel values on save", () => {
    expect(optionalTextForSave("")).toBeNull();
    expect(optionalTextForSave(UNSPECIFIED_FIELD_LABEL_HE)).toBeNull();
    expect(optionalTextForSave("לא מצוין")).toBeNull();
    expect(optionalTextForSave("  עו״ד כהן ")).toBe("עו״ד כהן");
  });
});
