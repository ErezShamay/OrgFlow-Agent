import { Capacitor } from "@capacitor/core";

export type ElayoAiCapacitorPlatform = "web" | "android" | "ios";

/** @deprecated Use `ElayoAiCapacitorPlatform`. */
export type OrgFlowCapacitorPlatform = ElayoAiCapacitorPlatform;

/** האם האפליקציה רצה בתוך WebView של Capacitor (לא דפדפן PWA רגיל). */
export function isCapacitorNativePlatform(): boolean {
  return Capacitor.isNativePlatform();
}

export function getCapacitorPlatform(): ElayoAiCapacitorPlatform {
  const platform = Capacitor.getPlatform();

  if (platform === "android" || platform === "ios") {
    return platform;
  }

  return "web";
}

export function isCapacitorAndroid(): boolean {
  return Capacitor.getPlatform() === "android";
}

/** WebView של APK (static export) — `https://localhost` / `http://localhost`. */
export function isCapacitorWebViewShell(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const { hostname, protocol } = window.location;
  if (hostname !== "localhost") {
    return false;
  }

  return protocol === "https:" || protocol === "http:";
}

/** שמירה/שחזור נתיב ומצלמה — native או WebView shell (גם לפני טעינת bridge). */
export function canUseCapacitorWebStorage(): boolean {
  return isCapacitorNativePlatform() || isCapacitorWebViewShell();
}
