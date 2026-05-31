import { describe, expect, it } from "vitest";

import {
  sortItems,
  toggleSortDirection,
} from "@/lib/ui/sorting";

describe("sorting", () => {
  it("sorts strings ascending and descending", () => {
    const items = [{ name: "Beta" }, { name: "Alpha" }];

    expect(
      sortItems(items, (item) => item.name, "asc").map(
        (item) => item.name
      )
    ).toEqual(["Alpha", "Beta"]);

    expect(
      sortItems(items, (item) => item.name, "desc").map(
        (item) => item.name
      )
    ).toEqual(["Beta", "Alpha"]);
  });

  it("toggles sort direction", () => {
    expect(toggleSortDirection("asc")).toBe("desc");
    expect(toggleSortDirection("desc")).toBe("asc");
  });
});
