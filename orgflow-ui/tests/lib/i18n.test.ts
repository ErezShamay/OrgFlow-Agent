import { describe, expect, it } from "vitest";

import {
  getDocumentDirection,
  translate,
} from "@/lib/ui/i18n";

describe("i18n", () => {
  it("translates keys per locale", () => {
    expect(translate("he", "common.loading")).toBe("טוען...");
    expect(translate("en", "common.loading")).toBe("Loading...");
  });

  it("resolves rtl and ltr directions", () => {
    expect(getDocumentDirection("he")).toBe("rtl");
    expect(getDocumentDirection("en")).toBe("ltr");
  });
});
