import { ELAYOAI_FIELD_REPORT_SYNC_ERRORS_KEY } from "@/lib/elayoai/keys";
import type { PendingSendSyncPhase } from "@/lib/field-reports/send-queue";

/** מפתח localStorage - טבעת שגיאות סנכרון (FR-037). */
export const FIELD_REPORT_SYNC_ERROR_LOG_KEY =
  ELAYOAI_FIELD_REPORT_SYNC_ERRORS_KEY;

export const FIELD_REPORT_SYNC_ERROR_LOG_MAX = 20;

export type FieldReportSyncErrorEvent = {
  organizationId: string;
  clientReportUuid: string;
  serverReportId?: string | null;
  phase: PendingSendSyncPhase;
  message: string;
  occurredAt: string;
};

export type FieldReportSentryConfig = {
  dsn: string | null;
  environment: string;
  enabled: boolean;
};

type SentryGlobal = {
  captureMessage?: (
    message: string,
    context?: {
      level?: string;
      tags?: Record<string, string>;
      extra?: Record<string, unknown>;
    }
  ) => void;
};

function readLocalStorage(): Storage | null {
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      return window.localStorage;
    }

    if (typeof localStorage !== "undefined") {
      return localStorage;
    }
  } catch {
    return null;
  }

  return null;
}

function parseStoredLog(raw: string | null): FieldReportSyncErrorEvent[] {
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter(
      (entry): entry is FieldReportSyncErrorEvent =>
        typeof entry === "object"
        && entry !== null
        && typeof (entry as FieldReportSyncErrorEvent).organizationId === "string"
        && typeof (entry as FieldReportSyncErrorEvent).clientReportUuid === "string"
        && typeof (entry as FieldReportSyncErrorEvent).message === "string"
    );
  } catch {
    return [];
  }
}

function writeStoredLog(entries: FieldReportSyncErrorEvent[]): void {
  const storage = readLocalStorage();
  if (!storage) {
    return;
  }

  storage.setItem(
    FIELD_REPORT_SYNC_ERROR_LOG_KEY,
    JSON.stringify(entries.slice(0, FIELD_REPORT_SYNC_ERROR_LOG_MAX))
  );
}

export function getFieldReportSentryConfig(
  env: NodeJS.ProcessEnv = process.env
): FieldReportSentryConfig {
  const dsn = env.NEXT_PUBLIC_SENTRY_DSN?.trim() || null;
  const environment =
    env.NEXT_PUBLIC_SENTRY_ENVIRONMENT?.trim()
    || env.NODE_ENV
    || "development";

  return {
    dsn,
    environment,
    enabled: Boolean(dsn),
  };
}

export function listFieldReportSyncErrorLog(): FieldReportSyncErrorEvent[] {
  const storage = readLocalStorage();
  if (!storage) {
    return [];
  }

  return parseStoredLog(storage.getItem(FIELD_REPORT_SYNC_ERROR_LOG_KEY));
}

export function clearFieldReportSyncErrorLog(): void {
  const storage = readLocalStorage();
  storage?.removeItem(FIELD_REPORT_SYNC_ERROR_LOG_KEY);
}

export function clearFieldReportSyncErrorsForOrganization(
  organizationId: string
): void {
  if (!organizationId) {
    return;
  }

  const remaining = listFieldReportSyncErrorLog().filter(
    (entry) => entry.organizationId !== organizationId
  );
  writeStoredLog(remaining);
}

export function clearFieldReportSyncErrorsForReport(
  organizationId: string,
  clientReportUuid: string
): void {
  if (!organizationId || !clientReportUuid) {
    return;
  }

  const remaining = listFieldReportSyncErrorLog().filter(
    (entry) =>
      entry.organizationId !== organizationId
      || entry.clientReportUuid !== clientReportUuid
  );
  writeStoredLog(remaining);
}

function appendLocalSyncError(event: FieldReportSyncErrorEvent): void {
  const storage = readLocalStorage();
  if (!storage) {
    return;
  }

  const next = [event, ...listFieldReportSyncErrorLog()].slice(
    0,
    FIELD_REPORT_SYNC_ERROR_LOG_MAX
  );
  writeStoredLog(next);
}

function parseSentryDsn(dsn: string): {
  storeUrl: string;
  publicKey: string;
} | null {
  try {
    const url = new URL(dsn);
    const projectId = url.pathname.replace(/^\//, "");
    const publicKey = url.username;

    if (!projectId || !publicKey) {
      return null;
    }

    return {
      storeUrl: `${url.protocol}//${url.host}/api/${projectId}/store/`,
      publicKey,
    };
  } catch {
    return null;
  }
}

function sentryGlobal(): SentryGlobal | null {
  if (typeof window === "undefined") {
    return null;
  }

  const candidate = (window as Window & { Sentry?: SentryGlobal }).Sentry;
  return candidate?.captureMessage ? candidate : null;
}

async function sendSyncErrorToSentryStore(
  event: FieldReportSyncErrorEvent,
  config: FieldReportSentryConfig
): Promise<void> {
  if (!config.dsn) {
    return;
  }

  const parsed = parseSentryDsn(config.dsn);
  if (!parsed) {
    return;
  }

  const eventId =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().replace(/-/g, "")
      : `${Date.now()}`.padStart(32, "0");

  await fetch(parsed.storeUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Sentry-Auth": `Sentry sentry_version=7, sentry_client=elayoai-field-reports/1.0, sentry_key=${parsed.publicKey}`,
    },
    body: JSON.stringify({
      event_id: eventId,
      message: event.message,
      level: "error",
      platform: "javascript",
      environment: config.environment,
      tags: {
        module: "field-reports",
        sync_phase: event.phase,
        organization_id: event.organizationId,
      },
      extra: {
        client_report_uuid: event.clientReportUuid,
        server_report_id: event.serverReportId ?? null,
      },
      timestamp: event.occurredAt,
    }),
    keepalive: true,
  });
}

function reportSyncErrorToSentry(event: FieldReportSyncErrorEvent): void {
  const sdk = sentryGlobal();
  if (sdk?.captureMessage) {
    sdk.captureMessage(event.message, {
      level: "error",
      tags: {
        module: "field-reports",
        sync_phase: event.phase,
        organization_id: event.organizationId,
      },
      extra: {
        client_report_uuid: event.clientReportUuid,
        server_report_id: event.serverReportId ?? null,
        occurred_at: event.occurredAt,
      },
    });
    return;
  }

  const config = getFieldReportSentryConfig();
  if (!config.enabled) {
    return;
  }

  void sendSyncErrorToSentryStore(event, config).catch(() => undefined);
}

/**
 * רושם שגיאת סנכרון - localStorage (טבעת) + Sentry אופציונלי (FR-037).
 * לא זורק - ניטור לא חוסם sync.
 */
export function recordFieldReportSyncError(
  input: Omit<FieldReportSyncErrorEvent, "occurredAt"> & {
    occurredAt?: string;
  }
): FieldReportSyncErrorEvent {
  const event: FieldReportSyncErrorEvent = {
    ...input,
    occurredAt: input.occurredAt ?? new Date().toISOString(),
  };

  appendLocalSyncError(event);
  reportSyncErrorToSentry(event);

  return event;
}

/** לאיפוס בין בדיקות יחידה. */
export function resetFieldReportSyncErrorMonitorForTests(): void {
  clearFieldReportSyncErrorLog();
}
