import type { Mock } from "vitest";

type ApiFetchMock = Mock<(path: string, init?: RequestInit) => Promise<Response>>;

export type FinalizeApiMockOptions = {
  reportId: string;
  finalizeStatus?: "FINALIZED" | "FINALIZE_FAILED";
  failFinalizePost?: boolean;
  failFinalizeMessage?: string;
};

export function matchFinalizeApi(
  path: string,
  init: RequestInit | undefined,
  options: FinalizeApiMockOptions
): Response | null {
  const { reportId } = options;
  const finalizeStatus = options.finalizeStatus ?? "FINALIZED";

  if (path.endsWith("/finalize") && init?.method === "POST") {
    if (options.failFinalizePost) {
      return {
        ok: false,
        json: async () => ({
          error: {
            message: options.failFinalizeMessage ?? "שליחה לליבה נכשלה",
            details: {
              error_code: "CORE_PIPELINE_FAILED",
            },
          },
        }),
      } as Response;
    }

    return {
      ok: true,
      json: async () => ({
        report_id: reportId,
        finalize_run_id: "finalize-run-test",
        status: "FINALIZING",
        message: "ok",
      }),
    } as Response;
  }

  if (path.endsWith("/finalize-status")) {
    return {
      ok: true,
      json: async () => ({
        report_id: reportId,
        status: finalizeStatus,
      }),
    } as Response;
  }

  return null;
}

export function mockFinalizeApiSuccess(
  apiFetch: ApiFetchMock,
  reportId: string,
  options?: Omit<FinalizeApiMockOptions, "reportId">
) {
  apiFetch.mockImplementation(async (path: string, init) => {
    const matched = matchFinalizeApi(path, init, {
      reportId,
      ...options,
    });
    if (matched) {
      return matched;
    }

    return { ok: true, json: async () => ({}) } as Response;
  });
}
