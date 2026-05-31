import { describe, expect, it } from "vitest";

import {
  getPageNumbers,
  paginateItems,
} from "@/lib/ui/pagination";

describe("pagination", () => {
  it("paginates items and reports navigation state", () => {
    const items = Array.from({ length: 25 }, (_, index) => index + 1);
    const result = paginateItems(items, 2, 10);

    expect(result.items).toEqual([11, 12, 13, 14, 15, 16, 17, 18, 19, 20]);
    expect(result.state.page).toBe(2);
    expect(result.totalPages).toBe(3);
    expect(result.hasNextPage).toBe(true);
    expect(result.hasPreviousPage).toBe(true);
  });

  it("builds visible page numbers", () => {
    expect(getPageNumbers(5, 10, 5)).toEqual([3, 4, 5, 6, 7]);
  });
});
