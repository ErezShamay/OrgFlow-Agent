import { readLinePhotoCaptureContext } from "@/lib/capacitor/line-photo-capture-context";
import {
  canUseCapacitorWebStorage,
  isCapacitorNativePlatform,
} from "@/lib/capacitor/platform";

export const CAPACITOR_LAST_ROUTE_STORAGE_KEY = "elayoai-capacitor-last-route";

function routeStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  if (!canUseCapacitorWebStorage() && !isCapacitorNativePlatform()) {
    return null;
  }

  return window.localStorage;
}

/** נתיב מלא כולל query - לשחזור אחרי מצלמה / reload של WebView. */
export function readCapacitorPersistedRoute(): string | null {
  const storage = routeStorage();
  if (!storage) {
    return null;
  }

  const raw = storage.getItem(CAPACITOR_LAST_ROUTE_STORAGE_KEY)?.trim();
  if (!raw || raw === "/") {
    return null;
  }

  return raw;
}

export function writeCapacitorPersistedRoute(path: string): void {
  if (typeof window === "undefined") {
    return;
  }

  const normalized = path.trim();
  if (!normalized || normalized === "/") {
    return;
  }

  try {
    window.localStorage.setItem(CAPACITOR_LAST_ROUTE_STORAGE_KEY, normalized);
  } catch {
    // WebView private mode / quota
  }
}

export function clearCapacitorPersistedRoute(): void {
  const storage = routeStorage();
  if (!storage) {
    return;
  }

  storage.removeItem(CAPACITOR_LAST_ROUTE_STORAGE_KEY);
}

export function currentDocumentPath(): string {
  if (typeof window === "undefined") {
    return "";
  }

  return `${window.location.pathname}${window.location.search}`;
}

export function isBootstrapCapacitorPath(pathname: string): boolean {
  const normalized = pathname.replace(/\/index\.html$/i, "") || "/";
  return normalized === "/" || normalized === "";
}

function isRestorableCapacitorTarget(target: string): boolean {
  return target.startsWith("/field-reports");
}

export function resolveCapacitorRestoreTarget(): string | null {
  const saved = readCapacitorPersistedRoute();
  if (saved) {
    return saved;
  }

  const pendingPhoto = readLinePhotoCaptureContext();
  return pendingPhoto?.returnPath?.trim() || null;
}

export function shouldRestoreCapacitorRoute(pathname: string): boolean {
  const target = resolveCapacitorRestoreTarget();
  if (!target || !isRestorableCapacitorTarget(target)) {
    return false;
  }

  return isBootstrapCapacitorPath(pathname);
}

/** ניווט חזרה לדוח - `location.replace` עובד אחרי reload ב-static export. */
export function restoreCapacitorRouteIfNeeded(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  if (!shouldRestoreCapacitorRoute(window.location.pathname)) {
    return false;
  }

  const target = resolveCapacitorRestoreTarget();
  if (!target || currentDocumentPath() === target) {
    return false;
  }

  window.location.replace(target);
  return true;
}
