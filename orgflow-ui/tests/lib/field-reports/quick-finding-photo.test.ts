import { describe, expect, it } from "vitest";

import {
  QUICK_FINDING_PHOTO_DESCRIPTION,
  QUICK_FINDING_PHOTO_TAP_COUNT,
  buildQuickFindingLinePayload,
  buildQuickFindingLocationFromGroup,
  formatQuickFindingDescription,
} from "@/lib/field-reports/quick-finding-photo";

describe("quick finding photo (3.1)", () => {
  it("documents the two-tap field flow", () => {
    expect(QUICK_FINDING_PHOTO_TAP_COUNT).toBe(2);
  });

  it("builds default quick finding description", () => {
    expect(formatQuickFindingDescription()).toBe(QUICK_FINDING_PHOTO_DESCRIPTION);
    expect(formatQuickFindingDescription(3)).toBe("ממצא מתמונה 3");
  });

  it("maps group selection to location on the new line", () => {
    expect(
      buildQuickFindingLocationFromGroup({ kind: "apartment", value: "12" })
    ).toBe("דירה 12");
  });

  it("builds a line payload ready for upsert with group fields", () => {
    const payload = buildQuickFindingLinePayload({
      lineId: "line-quick-1",
      group: { kind: "floor", value: "4" },
      sequence: 2,
    });

    expect(payload.client_line_uuid).toBe("line-quick-1");
    expect(payload.description).toBe("ממצא מתמונה 2");
    expect(payload.location).toBe("קומה 4");
    expect(payload.group_key).toBe("floor:4");
    expect(payload.group_label_he).toBe("קומה 4");
  });
});
