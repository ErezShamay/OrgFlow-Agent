import { describe, expect, it } from "vitest";

import { dashboardDynamicSegmentParams } from "@/lib/capacitor/static-export-params";

describe("dashboardDynamicSegmentParams", () => {
  it("returns empty on Vercel web build", () => {
    expect(
      dashboardDynamicSegmentParams({
        VERCEL: "1",
        ELAYOAI_CAPACITOR_BUILD: "static",
      })
    ).toEqual([]);
  });

  it("returns empty for default npm run build", () => {
    expect(dashboardDynamicSegmentParams({})).toEqual([]);
  });

  it("returns placeholder for explicit mobile static export", () => {
    expect(
      dashboardDynamicSegmentParams({
        ELAYOAI_CAPACITOR_BUILD: "static",
      })
    ).toEqual([{ id: "_" }]);
  });
});
