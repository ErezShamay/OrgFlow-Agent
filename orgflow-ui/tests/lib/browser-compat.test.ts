import { describe, expect, it } from "vitest";

import {
  detectBrowserSupport,
  getUnsupportedFeatures,
} from "@/lib/ui/browser-compat";

describe("browser compatibility", () => {
  it("detects feature support in node test runtime", () => {
    const support = detectBrowserSupport();

    expect(support.intersectionObserver).toBe(false);
    expect(support.localStorage).toBe(false);
  });

  it("lists unsupported features", () => {
    const unsupported = getUnsupportedFeatures({
      intersectionObserver: false,
      resizeObserver: true,
      webp: true,
      localStorage: false,
    });

    expect(unsupported).toEqual([
      "intersectionObserver",
      "localStorage",
    ]);
  });
});
