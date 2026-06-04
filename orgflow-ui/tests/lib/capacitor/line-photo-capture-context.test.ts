import { afterEach, describe, expect, it, vi } from "vitest";

import {
  clearLinePhotoCaptureContext,
  linePhotoCaptureResumeMessage,
  readLinePhotoCaptureContext,
  writeLinePhotoCaptureContext,
} from "@/lib/capacitor/line-photo-capture-context";

vi.mock("@/lib/capacitor/platform", () => ({
  isCapacitorNativePlatform: vi.fn(() => false),
  isCapacitorWebViewShell: vi.fn(() => true),
  canUseCapacitorWebStorage: vi.fn(() => true),
}));

function createLocalStorageMock() {
  const store = new Map<string, string>();

  return {
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
  };
}

describe("line photo capture context", () => {
  afterEach(() => {
    clearLinePhotoCaptureContext();
  });

  it("persists return path and line ids for resume after camera", () => {
    vi.stubGlobal("window", {
      localStorage: createLocalStorageMock(),
      location: {
        pathname: "/",
        search: "",
        protocol: "https:",
        hostname: "localhost",
      },
    });

    writeLinePhotoCaptureContext({
      returnPath: "/field-reports/_/?report=abc",
      reportId: "report-1",
      lineId: "line-1",
    });

    const saved = readLinePhotoCaptureContext();
    expect(saved?.returnPath).toBe("/field-reports/_/?report=abc");
    expect(saved?.reportId).toBe("report-1");
    expect(saved?.lineId).toBe("line-1");
  });

  it("linePhotoCaptureResumeMessage matches same line only", () => {
    vi.stubGlobal("window", {
      localStorage: createLocalStorageMock(),
      location: {
        pathname: "/",
        search: "",
        protocol: "https:",
        hostname: "localhost",
      },
    });

    writeLinePhotoCaptureContext({
      returnPath: "/field-reports/_/?report=abc",
      reportId: "report-1",
      lineId: "line-1",
    });

    const context = readLinePhotoCaptureContext();
    expect(context).not.toBeNull();
    expect(
      linePhotoCaptureResumeMessage(context!, "report-1", "line-1")
    ).toContain("צלם שוב");
    expect(
      linePhotoCaptureResumeMessage(context!, "report-1", "line-2")
    ).toBeNull();
  });
});
