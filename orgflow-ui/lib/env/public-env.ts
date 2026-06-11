import { isCapacitorAndroid } from "@/lib/capacitor/platform";

/**
 * Supabase ל-UI (anon בלבד).
 *
 * - בדפדפן Next.js חושף רק `NEXT_PUBLIC_*`.
 * - `SUPABASE_URL` / `SUPABASE_ANON_KEY` (בלי NEXT_PUBLIC) - fallback ל-SSR/build בלבד;
 *   לא מחליף את הצורך ב-NEXT_PUBLIC_* ב-Vercel ל-login בדפדפן.
 * - לעולם לא להשתמש ב-`SUPABASE_KEY` (service_role) כאן.
 */
export function getSupabasePublicConfig() {
  const url =
    process.env.NEXT_PUBLIC_SUPABASE_URL?.trim()
    || process.env.SUPABASE_URL?.trim()
    || "";

  const anonKey =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim()
    || process.env.SUPABASE_ANON_KEY?.trim()
    || "";

  return { url, anonKey };
}

export function isSupabaseConfigured(): boolean {
  const { url, anonKey } = getSupabasePublicConfig();
  return Boolean(url && anonKey);
}

/**
 * כתובת API שנקלעת ל-bundle ב-build.
 * ב-Android: `localhost` → `10.0.2.2` (אמולטור); במכשיר פיזי השתמשו ב-IP של המחשב ב-.env.
 */
export function getApiBaseUrl(): string {
  const configured =
    process.env.NEXT_PUBLIC_API_URL_ANDROID?.trim()
    || process.env.NEXT_PUBLIC_API_URL?.trim()
    || "http://localhost:8000";

  if (typeof window === "undefined" || !isCapacitorAndroid()) {
    return configured;
  }

  return configured
    .replace("://localhost", "://10.0.2.2")
    .replace("://127.0.0.1", "://10.0.2.2");
}

export function describeMobileAuthConfig(): string | null {
  const problems: string[] = [];

  if (!isSupabaseConfigured()) {
    problems.push(
      "חסרים NEXT_PUBLIC_SUPABASE_URL ו-NEXT_PUBLIC_SUPABASE_ANON_KEY (או SUPABASE_URL + SUPABASE_ANON_KEY ל-build)"
    );
  }

  if (typeof window !== "undefined" && isCapacitorAndroid()) {
    const raw =
      process.env.NEXT_PUBLIC_API_URL_ANDROID?.trim()
      || process.env.NEXT_PUBLIC_API_URL?.trim()
      || "";

    if (!raw || /localhost|127\.0\.0\.1/.test(raw)) {
      problems.push(
        "הגדירו ב-.env.capacitor.local את NEXT_PUBLIC_API_URL ל-IP המחשב (למשל http://192.168.1.10:3000) ובנו APK מחדש"
      );
    }
  }

  return problems.length > 0 ? problems.join(". ") : null;
}
