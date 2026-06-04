import { afterEach, describe, expect, it, vi } from "vitest";

import {
  clearCapacitorPersistedRoute,
  currentDocumentPath,
  isBootstrapCapacitorPath,
  readCapacitorPersistedRoute,
  resolveCapacitorRestoreTarget,
  shouldRestoreCapacitorRoute,
  writeCapacitorPersistedRoute,
} from "@/lib/capacitor/route-persistence";
import {
  clearLinePhotoCaptureContext,
  writeLinePhotoCaptureContext,
} from "@/lib/capacitor/line-photo-capture-context";

vi.mock("@/lib/capacitor/platform", () => ({
  isCapacitorNativePlatform: vi.fn(() => false),
  isCapacitorWebViewShell: vi.fn(() => true),
  canUseCapacitorWebStorage: vi.fn(() => true),
}));

function createCapacitorWindowMock(pathname = "/", search = "") {
  const store = new Map<string, string>();

  return {
    localStorage: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
      clear: () => {
        store.clear();
      },
    },
    location: {
      pathname,
      search,
      protocol: "https:",
      hostname: "localhost",
    },
  };
}

describe("capacitor route persistence", () => {
  afterEach(() => {
    vi.stubGlobal("window", createCapacitorWindowMock());
    clearCapacitorPersistedRoute();
    clearLinePhotoCaptureContext();
  });

  it("writes and reads field report path with query in localStorage", () => {
    vi.stubGlobal("window", createCapacitorWindowMock());

    writeCapacitorPersistedRoute(
      "/field-reports/_/?report=a1111111-1111-4111-8111-111111111111"
    );

    expect(readCapacitorPersistedRoute()).toBe(
      "/field-reports/_/?report=a1111111-1111-4111-8111-111111111111"
    );
  });

  it("shouldRestoreCapacitorRoute when on home with saved field report path", () => {
    vi.stubGlobal("window", createCapacitorWindowMock());

    writeCapacitorPersistedRoute("/field-reports/_/?report=abc");

    expect(shouldRestoreCapacitorRoute("/")).toBe(true);
    expect(shouldRestoreCapacitorRoute("/index.html")).toBe(true);
    expect(shouldRestoreCapacitorRoute("/field-reports/new")).toBe(false);
  });

  it("shouldRestore from pending camera context when route key is missing", () => {
    vi.stubGlobal("window", createCapacitorWindowMock());

    writeLinePhotoCaptureContext({
      returnPath: "/field-reports/_/?report=from-camera",
      reportId: "report-1",
      lineId: "line-1",
    });

    expect(resolveCapacitorRestoreTarget()).toBe(
      "/field-reports/_/?report=from-camera"
    );
    expect(shouldRestoreCapacitorRoute("/")).toBe(true);
  });

  it("isBootstrapCapacitorPath detects home and index.html", () => {
    expect(isBootstrapCapacitorPath("/")).toBe(true);
    expect(isBootstrapCapacitorPath("/index.html")).toBe(true);
    expect(isBootstrapCapacitorPath("/field-reports/_/")).toBe(false);
  });

  it("currentDocumentPath includes search params", () => {
    vi.stubGlobal(
      "window",
      createCapacitorWindowMock("/field-reports/_/", "?report=abc")
    );

    expect(currentDocumentPath()).toBe("/field-reports/_/?report=abc");
  });
});
