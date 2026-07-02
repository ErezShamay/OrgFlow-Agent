import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import {
  enqueuePendingSendRequest,
  loadPendingSendRequests,
} from "@/lib/field-reports/send-queue";
import { stubBrowserStorage } from "../helpers/browser-storage-mock";
import { matchFinalizeApi } from "../helpers/mock-finalize-api";

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
  deleteVisitReportPdfLocally: vi.fn(async () => undefined),
}));

describe("process-send-queue", () => {
  beforeEach(async () => {
    stubBrowserStorage();
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("processes queued send through metadata, photos, pdf, and finalize", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      const finalize = matchFinalizeApi(path, init, { reportId: "report-a" });
      if (finalize) {
        return finalize;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    const { processPendingSendRequest } = await import(
      "@/lib/field-reports/process-send-queue"
    );

    const queued = await enqueuePendingSendRequest("org-1", "report-a");

    const result = await processPendingSendRequest(queued);

    expect(result.success).toBe(true);
    expect(await loadPendingSendRequests("org-1")).toHaveLength(0);
    expect(apiFetch).toHaveBeenCalledWith(
      "/field-reports/visits/report-a/finalize",
      expect.objectContaining({
        method: "POST",
        headers: {
          "X-Idempotency-Key": queued.idempotencyKey,
        },
      })
    );

    const callArgs = vi.mocked(apiFetch).mock.calls[0]?.[1];
    expect(callArgs?.body).toBeInstanceOf(FormData);
  });

  it("keeps queue entry when finalize does not complete successfully", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      const finalize = matchFinalizeApi(path, init, {
        reportId: "report-a",
        finalizeStatus: "FINALIZE_FAILED",
      });
      if (finalize) {
        return finalize;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    const { processPendingSendRequest } = await import(
      "@/lib/field-reports/process-send-queue"
    );

    const queued = await enqueuePendingSendRequest("org-1", "report-a");
    const result = await processPendingSendRequest(queued);

    expect(result.success).toBe(false);
    expect(result.error).toContain("עיבוד הדוח נכשל");

    const [entry] = await loadPendingSendRequests("org-1");
    expect(entry.reportId).toBe("report-a");
    expect(entry.syncPhase).toBe("finalize");
    expect(entry.lastError).toContain("עיבוד הדוח נכשל");
  });

  it("stores finalize error with API error code for retry", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      const finalize = matchFinalizeApi(path, init, {
        reportId: "report-a",
        failFinalizePost: true,
        failFinalizeMessage: "שליחה לליבה נכשלה",
      });
      if (finalize) {
        return finalize;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    const { processPendingSendRequest } = await import(
      "@/lib/field-reports/process-send-queue"
    );

    const queued = await enqueuePendingSendRequest("org-1", "report-a");
    const result = await processPendingSendRequest(queued);

    expect(result.success).toBe(false);
    expect(result.error).toContain("שליחה לליבה נכשלה");

    const [entry] = await loadPendingSendRequests("org-1");
    expect(entry.reportId).toBe("report-a");
    expect(entry.syncPhase).toBe("finalize");
    expect(entry.lastError).toContain("שליחה לליבה נכשלה");
  });

  it("retries after failure without changing idempotency key", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    let finalizeCalls = 0;

    vi.mocked(apiFetch).mockImplementation(async (path: string, init) => {
      if (path.endsWith("/finalize") && init?.method === "POST") {
        finalizeCalls += 1;
        if (finalizeCalls === 1) {
          return {
            ok: false,
            json: async () => ({
              error: { message: "שגיאה זמנית" },
            }),
          } as Response;
        }
      }

      const finalize = matchFinalizeApi(path, init, { reportId: "report-a" });
      if (finalize) {
        return finalize;
      }

      return { ok: true, json: async () => ({}) } as Response;
    });

    const { processPendingSendRequest } = await import(
      "@/lib/field-reports/process-send-queue"
    );

    const queued = await enqueuePendingSendRequest("org-1", "report-a");
    const firstKey = queued.idempotencyKey;

    const first = await processPendingSendRequest(queued);
    expect(first.success).toBe(false);

    const [afterFail] = await loadPendingSendRequests("org-1");
    expect(afterFail.idempotencyKey).toBe(firstKey);

    const second = await processPendingSendRequest(afterFail);
    expect(second.success).toBe(true);
    expect(finalizeCalls).toBe(2);
    expect(await loadPendingSendRequests("org-1")).toHaveLength(0);

    const finalizeCallsMade = vi.mocked(apiFetch).mock.calls.filter(
      (call) =>
        typeof call[0] === "string" && call[0].endsWith("/finalize")
    );
    expect(finalizeCallsMade).toHaveLength(2);
    expect(
      (finalizeCallsMade[0]?.[1]?.headers as Record<string, string>)?.[
        "X-Idempotency-Key"
      ]
    ).toBe(firstKey);
    expect(
      (finalizeCallsMade[1]?.[1]?.headers as Record<string, string>)?.[
        "X-Idempotency-Key"
      ]
    ).toBe(firstKey);
  });
});
