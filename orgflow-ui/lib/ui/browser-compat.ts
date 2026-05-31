export type BrowserFeatureSupport = {
  intersectionObserver: boolean;
  resizeObserver: boolean;
  webp: boolean;
  localStorage: boolean;
};

export function detectBrowserSupport(): BrowserFeatureSupport {
  const hasWindow = typeof window !== "undefined";

  return {
    intersectionObserver:
      hasWindow && "IntersectionObserver" in window,
    resizeObserver:
      hasWindow && "ResizeObserver" in window,
    webp:
      hasWindow &&
      document
        .createElement("canvas")
        .toDataURL("image/webp")
        .startsWith("data:image/webp"),
    localStorage: hasWindow && (() => {
      try {
        const key = "__of_test__";
        window.localStorage.setItem(key, "1");
        window.localStorage.removeItem(key);
        return true;
      } catch {
        return false;
      }
    })(),
  };
}

export function getUnsupportedFeatures(
  support: BrowserFeatureSupport
): string[] {
  const unsupported: string[] = [];

  if (!support.intersectionObserver) {
    unsupported.push("intersectionObserver");
  }

  if (!support.resizeObserver) {
    unsupported.push("resizeObserver");
  }

  if (!support.localStorage) {
    unsupported.push("localStorage");
  }

  return unsupported;
}
