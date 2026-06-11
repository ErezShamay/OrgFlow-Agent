import { apiFetch } from "@/lib/api/client";
import {
  readCapacitorNetworkConnectedSync,
  refreshCapacitorNetworkStatus,
  subscribeCapacitorNetworkConnectivity,
  useCapacitorFieldReportNetwork,
} from "@/lib/capacitor/field-report-network";

export type FieldReportNetworkSnapshot = {
  navigatorOnline: boolean;
  apiReachable: boolean;
};

export const FIELD_REPORTS_PING_PATH = "/field-reports/module-status";

export const DEFAULT_FIELD_REPORT_PING_TIMEOUT_MS = 5000;

/** מרווח בדיקה תקופית (PWA + ping; native - גם Capacitor Network events). */
export const DEFAULT_FIELD_REPORT_NETWORK_POLL_MS = 120_000;

export type FieldReportNetworkConnectivity =
  | "offline"
  | "captive"
  | "online";

export type FieldReportPingRequest = (
  signal: AbortSignal
) => Promise<Response>;

export type FieldReportNetworkSource = {
  readNavigatorOnline?: () => boolean;
  ping?: FieldReportPingRequest;
};

export type ProbeFieldReportNetworkOptions = {
  timeoutMs?: number;
  request?: FieldReportPingRequest;
  readNavigatorOnline?: () => boolean;
};

function defaultFieldReportPingRequest(
  signal: AbortSignal
): Promise<Response> {
  return apiFetch(FIELD_REPORTS_PING_PATH, {
    method: "GET",
    signal,
  });
}

export function readNavigatorOnline(
  read?: () => boolean
): boolean {
  if (read) {
    return read();
  }

  if (useCapacitorFieldReportNetwork()) {
    const cached = readCapacitorNetworkConnectedSync();
    if (cached !== null) {
      return cached;
    }
  }

  if (typeof navigator === "undefined") {
    return true;
  }

  return navigator.onLine;
}

/**
 * Ping קל ל-`/field-reports/module-status` - בודק שה-API זמין (לא רק `navigator.onLine`).
 */
export async function pingFieldReportsApi(options?: {
  timeoutMs?: number;
  request?: FieldReportPingRequest;
  readNavigatorOnline?: () => boolean;
}): Promise<boolean> {
  if (!readNavigatorOnline(options?.readNavigatorOnline)) {
    return false;
  }

  const controller = new AbortController();
  const timeoutMs = options?.timeoutMs ?? DEFAULT_FIELD_REPORT_PING_TIMEOUT_MS;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  const request = options?.request ?? defaultFieldReportPingRequest;

  try {
    const response = await request(controller.signal);
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeoutId);
  }
}

export function resolveFieldReportConnectivity(
  snapshot: FieldReportNetworkSnapshot
): FieldReportNetworkConnectivity {
  if (!snapshot.navigatorOnline) {
    return "offline";
  }

  if (!snapshot.apiReachable) {
    return "captive";
  }

  return "online";
}

/**
 * בדיקת רשת מלאה - `navigator` + ping (מקור אמת לסנכרון ול-data-source).
 */
export async function probeFieldReportNetworkStatus(
  options?: ProbeFieldReportNetworkOptions
): Promise<FieldReportNetworkSnapshot> {
  if (
    useCapacitorFieldReportNetwork()
    && !options?.readNavigatorOnline
  ) {
    await refreshCapacitorNetworkStatus();
  }

  const navigatorOnline = readNavigatorOnline(
    options?.readNavigatorOnline
  );

  if (!navigatorOnline) {
    return {
      navigatorOnline: false,
      apiReachable: false,
    };
  }

  const apiReachable = await pingFieldReportsApi(options);

  return {
    navigatorOnline: true,
    apiReachable,
  };
}

/** האם מותר להריץ `SyncManager` (API נגיש, לא רק Wi‑Fi מקומי). */
export function canRunFieldReportSync(
  snapshot: FieldReportNetworkSnapshot
): boolean {
  return snapshot.navigatorOnline && snapshot.apiReachable;
}

export function fieldReportNetworkStatusLabelHe(
  connectivity: FieldReportNetworkConnectivity
): string {
  switch (connectivity) {
    case "offline":
      return "אין חיבור רשת";
    case "captive":
      return "רשת מקומית - השרת לא נגיש";
    case "online":
      return "מחובר לשרת";
  }
}

export type FieldReportNetworkStatusListener = (
  snapshot: FieldReportNetworkSnapshot
) => void;

/**
 * מאזין לשינויי רשת - `online` + בדיקה תקופית (§7 ג.8).
 * מחזיר פונקציית ביטול.
 */
export function subscribeFieldReportNetworkStatus(
  listener: FieldReportNetworkStatusListener,
  options?: ProbeFieldReportNetworkOptions & {
    pollIntervalMs?: number;
  }
): () => void {
  if (typeof window === "undefined") {
    void probeFieldReportNetworkStatus(options).then(listener);
    return () => undefined;
  }

  let cancelled = false;

  const emit = async () => {
    if (cancelled) {
      return;
    }

    const snapshot = await probeFieldReportNetworkStatus(options);
    if (!cancelled) {
      listener(snapshot);
    }
  };

  void emit();

  const handleConnectivityChange = () => {
    void emit();
  };

  const useNativeNetwork = useCapacitorFieldReportNetwork();
  const unsubscribeCapacitor = useNativeNetwork
    ? subscribeCapacitorNetworkConnectivity(handleConnectivityChange)
    : () => undefined;

  if (!useNativeNetwork) {
    window.addEventListener("online", handleConnectivityChange);
    window.addEventListener("offline", handleConnectivityChange);
  }

  const pollIntervalMs =
    options?.pollIntervalMs ?? DEFAULT_FIELD_REPORT_NETWORK_POLL_MS;
  const intervalId = window.setInterval(() => {
    void emit();
  }, pollIntervalMs);

  return () => {
    cancelled = true;
    unsubscribeCapacitor();

    if (!useNativeNetwork) {
      window.removeEventListener("online", handleConnectivityChange);
      window.removeEventListener("offline", handleConnectivityChange);
    }

    window.clearInterval(intervalId);
  };
}
