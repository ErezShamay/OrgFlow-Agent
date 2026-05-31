import { describe, expect, it } from "vitest";

import { createLazyLoader } from "@/lib/ui/lazy";

describe("lazy loading", () => {
  it("caches loader results", async () => {
    let calls = 0;
    const load = createLazyLoader(async () => {
      calls += 1;
      return { value: 42 };
    });

    await load();
    await load();

    expect(calls).toBe(1);
  });
});
