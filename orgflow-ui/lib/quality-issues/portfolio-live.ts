/**
 * R1 — live portfolio counters via SSE (/portfolio/events) or 30s polling fallback.
 */

import { apiFetch } from "@/lib/api/client";

export const PORTFOLIO_LIVE_POLL_INTERVAL_MS = 30_000;

export type QualityPortfolioLiveSnapshot = {
  organization_id: string;
  total_open: number;
  total_open_critical: number;
  updated_at: string;
};

export type PortfolioLiveConnection = {
  stop: () => void;
};

export function buildPortfolioLiveSnapshotPath(): string {
  return "/portfolio/live-snapshot";
}

export function buildPortfolioEventsPath(): string {
  return "/portfolio/events";
}

export function parsePortfolioLiveSnapshot(
  value: unknown
): QualityPortfolioLiveSnapshot {
  if (!value || typeof value !== "object") {
    throw new Error("Invalid portfolio live snapshot payload");
  }

  const record = value as Record<string, unknown>;

  return {
    organization_id:
      typeof record.organization_id === "string" ? record.organization_id : "",
    total_open:
      typeof record.total_open === "number" ? record.total_open : 0,
    total_open_critical:
      typeof record.total_open_critical === "number"
        ? record.total_open_critical
        : 0,
    updated_at:
      typeof record.updated_at === "string" ? record.updated_at : "",
  };
}

export async function getPortfolioLiveSnapshot(): Promise<QualityPortfolioLiveSnapshot> {
  const response = await apiFetch(buildPortfolioLiveSnapshotPath());

  if (!response.ok) {
    throw new Error(`Portfolio live snapshot failed (${response.status})`);
  }

  return parsePortfolioLiveSnapshot(await response.json());
}

type ParsedSseChunk = {
  events: string[];
  remainder: string;
};

export function parseSseDataLines(buffer: string): ParsedSseChunk {
  const events: string[] = [];
  const blocks = buffer.split("\n\n");
  const remainder = blocks.pop() ?? "";

  for (const block of blocks) {
    const dataLines = block
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.replace(/^data:\s?/, ""));

    if (dataLines.length > 0) {
      events.push(dataLines.join("\n"));
    }
  }

  return { events, remainder };
}

export function connectPortfolioLiveUpdates(
  onSnapshot: (snapshot: QualityPortfolioLiveSnapshot) => void,
  options?: {
    onError?: (error: Error) => void;
  }
): PortfolioLiveConnection {
  let stopped = false;
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let abortController: AbortController | null = null;

  const notifyError = (error: unknown) => {
    const normalized =
      error instanceof Error ? error : new Error(String(error));
    options?.onError?.(normalized);
  };

  const applySnapshot = (snapshot: QualityPortfolioLiveSnapshot) => {
    if (!stopped) {
      onSnapshot(snapshot);
    }
  };

  const startPolling = () => {
    if (pollTimer || stopped) {
      return;
    }

    const poll = async () => {
      try {
        applySnapshot(await getPortfolioLiveSnapshot());
      } catch (error) {
        notifyError(error);
      }
    };

    void poll();
    pollTimer = window.setInterval(() => {
      void poll();
    }, PORTFOLIO_LIVE_POLL_INTERVAL_MS);
  };

  const startSse = async () => {
    abortController = new AbortController();

    try {
      const response = await apiFetch(buildPortfolioEventsPath(), {
        headers: {
          Accept: "text/event-stream",
        },
        signal: abortController.signal,
      });

      if (!response.ok || !response.body) {
        startPolling();
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (!stopped) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const { events, remainder } = parseSseDataLines(buffer);
        buffer = remainder;

        for (const data of events) {
          try {
            applySnapshot(
              parsePortfolioLiveSnapshot(JSON.parse(data))
            );
          } catch (error) {
            notifyError(error);
          }
        }
      }

      if (!stopped) {
        startPolling();
      }
    } catch (error) {
      if (stopped) {
        return;
      }

      if (
        error instanceof DOMException
        && error.name === "AbortError"
      ) {
        return;
      }

      startPolling();
    }
  };

  void startSse();

  return {
    stop: () => {
      stopped = true;
      abortController?.abort();
      if (pollTimer) {
        window.clearInterval(pollTimer);
      }
    },
  };
}
