import { Network } from "@capacitor/network";
import type { PluginListenerHandle } from "@capacitor/core";

import { isCapacitorNativePlatform } from "@/lib/capacitor/platform";

let connectedCache: boolean | null = null;
let watchStarted = false;
let watchPromise: Promise<void> | null = null;
let nativeListener: PluginListenerHandle | null = null;

const connectivityListeners = new Set<(connected: boolean) => void>();

/** מקור `navigatorOnline` ב-APK - `@capacitor/network` (FR-033). */
export function isCapacitorFieldReportNetwork(): boolean {
  return isCapacitorNativePlatform();
}

export function readCapacitorNetworkConnectedSync(): boolean | null {
  return connectedCache;
}

export async function refreshCapacitorNetworkStatus(): Promise<boolean> {
  if (!isCapacitorFieldReportNetwork()) {
    if (typeof navigator === "undefined") {
      return true;
    }

    return navigator.onLine;
  }

  const status = await Network.getStatus();
  connectedCache = status.connected;
  return status.connected;
}

function notifyConnectivityListeners(connected: boolean): void {
  for (const listener of connectivityListeners) {
    listener(connected);
  }
}

async function ensureCapacitorNetworkWatch(): Promise<void> {
  if (!isCapacitorFieldReportNetwork() || watchStarted) {
    return;
  }

  if (!watchPromise) {
    watchPromise = (async () => {
      await refreshCapacitorNetworkStatus();
      nativeListener = await Network.addListener(
        "networkStatusChange",
        (status) => {
          connectedCache = status.connected;
          notifyConnectivityListeners(status.connected);
        }
      );
      watchStarted = true;
    })();
  }

  await watchPromise;
}

/**
 * מאזין לשינויי חיבור ב-native. ב-web - מחזיר ביטול ריק (הקורא משתמש ב-window).
 */
export function subscribeCapacitorNetworkConnectivity(
  listener: (connected: boolean) => void
): () => void {
  if (!isCapacitorFieldReportNetwork()) {
    return () => undefined;
  }

  connectivityListeners.add(listener);
  void ensureCapacitorNetworkWatch().then(() => {
    if (connectedCache !== null) {
      listener(connectedCache);
    }
  });

  return () => {
    connectivityListeners.delete(listener);
  };
}

/** לאיפוס בין בדיקות יחידה. */
export function resetCapacitorFieldReportNetworkForTests(): void {
  connectedCache = null;
  watchStarted = false;
  watchPromise = null;
  connectivityListeners.clear();
  void nativeListener?.remove();
  nativeListener = null;
}
