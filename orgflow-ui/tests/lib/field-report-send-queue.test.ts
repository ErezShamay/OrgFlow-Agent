import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearAllPendingSendRequests,
  enqueuePendingSendRequest,
  loadPendingSendRequests,
  pendingSendPhaseLabelHe,
  removePendingSendRequest,
  updatePendingSendRequest,
} from "@/lib/field-reports/send-queue";

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

describe("send-queue", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", createLocalStorageMock());
    vi.stubGlobal("window", { localStorage: createLocalStorageMock() });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("enqueues and removes pending send requests per organization", () => {
    enqueuePendingSendRequest("org-1", "report-a");
    enqueuePendingSendRequest("org-1", "report-b");

    expect(loadPendingSendRequests("org-1")).toHaveLength(2);

    removePendingSendRequest("org-1", "report-a");
    expect(loadPendingSendRequests("org-1")).toHaveLength(1);
    expect(loadPendingSendRequests("org-1")[0].reportId).toBe("report-b");
  });

  it("replaces an existing queue entry for the same report", () => {
    const first = enqueuePendingSendRequest("org-1", "report-a");
    updatePendingSendRequest("org-1", "report-a", {
      syncPhase: "photos",
      lastError: "retry",
    });
    enqueuePendingSendRequest("org-1", "report-a");

    const [entry] = loadPendingSendRequests("org-1");
    expect(entry.syncPhase).toBe("queued");
    expect(entry.lastError).toBeUndefined();
    expect(entry.idempotencyKey).toBe(first.idempotencyKey);
  });

  it("maps sync phases to Hebrew labels", () => {
    expect(pendingSendPhaseLabelHe("photos")).toContain("תמונות");
    expect(pendingSendPhaseLabelHe("request_send")).toContain("ליבה");
  });

  it("cancels pending send for one report without touching other reports (3D.7)", () => {
    enqueuePendingSendRequest("org-1", "report-a");
    enqueuePendingSendRequest("org-1", "report-b");

    removePendingSendRequest("org-1", "report-a");

    const remaining = loadPendingSendRequests("org-1");
    expect(remaining).toHaveLength(1);
    expect(remaining[0].reportId).toBe("report-b");
  });

  it("clears all pending sends for an organization", () => {
    enqueuePendingSendRequest("org-1", "report-a");
    enqueuePendingSendRequest("org-1", "report-b");
    enqueuePendingSendRequest("org-2", "report-c");

    clearAllPendingSendRequests("org-1");

    expect(loadPendingSendRequests("org-1")).toHaveLength(0);
    expect(loadPendingSendRequests("org-2")).toHaveLength(1);
  });
});

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

vi.mock("@/lib/field-reports/report-metadata-draft", () => ({
  flushReportMetadataDraft: vi.fn(async () => undefined),
}));

vi.mock("@/lib/field-reports/sync-pending-line-photos", () => ({
  syncPendingLinePhotosForReport: vi.fn(async () => ({
    uploaded: 0,
    failed: [],
  })),
}));

vi.mock("@/lib/field-reports/pdf/visit-report-pdf-store", () => ({
  hasVisitReportPdfLocally: vi.fn(async () => true),
  loadVisitReportPdfLocally: vi.fn(async () => ({
    reportId: "report-a",
    blob: new Blob(["pdf-content"], { type: "application/pdf" }),
    filename: "report-a.pdf",
    generatedAt: new Date().toISOString(),
  })),
}));

describe("process-send-queue", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", createLocalStorageMock());
    vi.stubGlobal("window", { localStorage: createLocalStorageMock() });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("processes queued send through metadata, photos, pdf, and request-send", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      if (path.endsWith("/request-send") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ id: "report-a", status: "LOCKED" }),
        } as Response;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    const { processPendingSendRequest } = await import(
      "@/lib/field-reports/process-send-queue"
    );

    enqueuePendingSendRequest("org-1", "report-a");

    const result = await processPendingSendRequest({
      reportId: "report-a",
      organizationId: "org-1",
      requestedAt: new Date().toISOString(),
      idempotencyKey: "idem-report-a",
      syncPhase: "queued",
    });

    expect(result.success).toBe(true);
    expect(loadPendingSendRequests("org-1")).toHaveLength(0);
    expect(apiFetch).toHaveBeenCalledWith(
      "/field-reports/visits/report-a/request-send",
      expect.objectContaining({
        method: "POST",
        headers: {
          "X-Idempotency-Key": "idem-report-a",
        },
      })
    );

    const callArgs = vi.mocked(apiFetch).mock.calls[0]?.[1];
    expect(callArgs?.body).toBeInstanceOf(FormData);
  });

  it("keeps queue entry when server does not return LOCKED", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      if (path.endsWith("/request-send") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ id: "report-a", status: "CLOSED" }),
        } as Response;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    const { processPendingSendRequest } = await import(
      "@/lib/field-reports/process-send-queue"
    );

    enqueuePendingSendRequest("org-1", "report-a");
    const result = await processPendingSendRequest({
      reportId: "report-a",
      organizationId: "org-1",
      requestedAt: new Date().toISOString(),
      idempotencyKey: "idem-report-a",
      syncPhase: "queued",
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain("לא אישר נעילת דוח");

    const [entry] = loadPendingSendRequests("org-1");
    expect(entry.reportId).toBe("report-a");
    expect(entry.syncPhase).toBe("request_send");
    expect(entry.lastError).toContain("לא אישר נעילת דוח");
  });

  it("stores request-send error with API error code for retry", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      if (path.endsWith("/request-send") && init?.method === "POST") {
        return {
          ok: false,
          json: async () => ({
            error: {
              message: "שליחה לליבה נכשלה",
              details: {
                error_code: "CORE_PIPELINE_FAILED",
              },
            },
          }),
        } as Response;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    const { processPendingSendRequest } = await import(
      "@/lib/field-reports/process-send-queue"
    );

    enqueuePendingSendRequest("org-1", "report-a");
    const result = await processPendingSendRequest({
      reportId: "report-a",
      organizationId: "org-1",
      requestedAt: new Date().toISOString(),
      idempotencyKey: "idem-report-a",
      syncPhase: "queued",
    });

    expect(result.success).toBe(false);
    expect(result.error).toContain("CORE_PIPELINE_FAILED");

    const [entry] = loadPendingSendRequests("org-1");
    expect(entry.reportId).toBe("report-a");
    expect(entry.syncPhase).toBe("request_send");
    expect(entry.lastError).toContain("CORE_PIPELINE_FAILED");
  });

  it("retries after failure without changing idempotency key", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    let requestSendCalls = 0;
    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      if (path.endsWith("/request-send") && init?.method === "POST") {
        requestSendCalls += 1;
        const headers = init?.headers as Record<string, string>;
        const idempotencyKey = headers?.["X-Idempotency-Key"];

        if (requestSendCalls === 1) {
          return {
            ok: false,
            json: async () => ({
              error: {
                message: "שליחה לליבה נכשלה",
                details: {
                  error_code: "TRANSIENT_CORE_ERROR",
                },
              },
              // Ensure mock uses the same idempotency key (helps catch regressions).
              idempotencyKey,
            }),
          } as Response;
        }

        return {
          ok: true,
          json: async () => ({ id: "report-a", status: "LOCKED" }),
        } as Response;
      }

      return { ok: true, json: async () => ({}) } as Response;
    });

    const { processPendingSendRequest } = await import(
      "@/lib/field-reports/process-send-queue"
    );

    enqueuePendingSendRequest("org-1", "report-a");
    const [firstEntry] = loadPendingSendRequests("org-1");
    const firstKey = firstEntry.idempotencyKey;

    const result1 = await processPendingSendRequest(firstEntry);
    expect(result1.success).toBe(false);

    const [afterFail] = loadPendingSendRequests("org-1");
    expect(afterFail.idempotencyKey).toBe(firstKey);
    expect(afterFail.lastError).toContain("TRANSIENT_CORE_ERROR");

    const result2 = await processPendingSendRequest(afterFail);
    expect(result2.success).toBe(true);
    expect(loadPendingSendRequests("org-1")).toHaveLength(0);

    const requestSendCallsArgs = vi.mocked(apiFetch).mock.calls.filter(
      (call) =>
        typeof call[0] === "string" && call[0].endsWith("/request-send")
    );

    const key1 = (requestSendCallsArgs[0][1]?.headers as Record<
      string,
      string
    >)?.["X-Idempotency-Key"];
    const key2 = (requestSendCallsArgs[1][1]?.headers as Record<
      string,
      string
    >)?.["X-Idempotency-Key"];

    expect(key1).toBe(firstKey);
    expect(key2).toBe(firstKey);
  });
});
