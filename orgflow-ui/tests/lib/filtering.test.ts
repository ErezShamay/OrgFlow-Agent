import { describe, expect, it } from "vitest";

import {
  buildSearchFilter,
  filterItems,
  matchesFilterRule,
} from "@/lib/ui/filtering";

describe("filtering", () => {
  it("matches filter operators", () => {
    expect(
      matchesFilterRule("Alpha Tower", {
        field: "name",
        operator: "contains",
        value: "tower",
      })
    ).toBe(true);
  });

  it("filters items by multiple rules", () => {
    const items = [
      { name: "Alpha", status: "ACTIVE" },
      { name: "Beta", status: "COMPLETED" },
    ];

    const filtered = filterItems(
      items,
      [
        {
          field: "status",
          operator: "equals",
          value: "active",
        },
      ],
      (item, field) => item[field]
    );

    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.name).toBe("Alpha");
  });

  it("builds search filters only when query exists", () => {
    expect(buildSearchFilter("name", "")).toEqual([]);
    expect(buildSearchFilter("name", "alpha")).toHaveLength(1);
  });
});
