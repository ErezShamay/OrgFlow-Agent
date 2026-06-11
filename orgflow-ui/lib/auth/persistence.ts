import { isCapacitorNativePlatform } from "@/lib/capacitor/platform";

/** Native app - שמירת התחברות בין הפעלות. דפדפן - סשן לכל טאב, נמחק בסגירת הטאב. */
export function shouldPersistAuthAcrossBrowserRestarts(): boolean {
  if (typeof window === "undefined") {
    return true;
  }

  return isCapacitorNativePlatform();
}

export function getSupabaseAuthStorage(): Storage | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }

  return shouldPersistAuthAcrossBrowserRestarts()
    ? window.localStorage
    : window.sessionStorage;
}

export function isSupabaseAuthStorageKey(key: string): boolean {
  return key.startsWith("sb-") && key.includes("-auth-token");
}

export function clearSupabaseAuthTokensFromStorage(storage: Storage): void {
  const keys: string[] = [];

  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    if (key && isSupabaseAuthStorageKey(key)) {
      keys.push(key);
    }
  }

  for (const key of keys) {
    storage.removeItem(key);
  }
}

/** מסיר סשן Supabase ישן מ-localStorage אחרי מעבר ל-sessionStorage בדפדפן. */
export function clearLegacySupabaseAuthFromLocalStorage(): void {
  if (typeof window === "undefined") {
    return;
  }

  clearSupabaseAuthTokensFromStorage(window.localStorage);
}

export function purgeWebTabAuthStorage(): void {
  if (typeof window === "undefined") {
    return;
  }

  clearSupabaseAuthTokensFromStorage(window.sessionStorage);
  clearLegacySupabaseAuthFromLocalStorage();
}
