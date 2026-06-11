/**
 * מצבי build ל-APK (FR-030).
 *
 * - **static (B)** - ברירת מחדל: `next build` עם `output: 'export'` → `out/` בתוך APK.
 *   מתאים לעבודה אופליין בשטח (IndexedDB + sync).
 * - **url (A)** - WebView טוען URL פרוס (staging/prod); `webDir` נשאר שלד ל-`cap sync`.
 */

export type CapacitorBuildMode = "static" | "url";

export const CAPACITOR_STATIC_EXPORT_PLACEHOLDER_ID = "_";

/** מזהה placeholder ל-`generateStaticParams` - ניווט ל-UUID אמיתי בצד לקוח. */
export function capacitorStaticExportParams(): Array<{ id: string }> {
  return [{ id: CAPACITOR_STATIC_EXPORT_PLACEHOLDER_ID }];
}

export function parseCapacitorBuildMode(
  raw: string | undefined
): CapacitorBuildMode {
  const normalized = raw?.trim().toLowerCase();

  if (
    normalized === "url"
    || normalized === "a"
    || normalized === "webview"
  ) {
    return "url";
  }

  return "static";
}

export function getCapacitorBuildMode(
  env: NodeJS.ProcessEnv = process.env
): CapacitorBuildMode {
  return parseCapacitorBuildMode(
    env.ELAYOAI_CAPACITOR_BUILD_MODE
    || env.ELAYOAI_CAPACITOR_BUILD
    || env.ORGFLOW_CAPACITOR_BUILD_MODE
    || env.ORGFLOW_CAPACITOR_BUILD
  );
}

export function isCapacitorStaticExportBuild(
  env: NodeJS.ProcessEnv = process.env
): boolean {
  if (
    env.ELAYOAI_CAPACITOR_BUILD === "static"
    || env.ORGFLOW_CAPACITOR_BUILD === "static"
  ) {
    return true;
  }

  return getCapacitorBuildMode(env) === "static";
}

export function getCapacitorServerUrl(
  env: NodeJS.ProcessEnv = process.env
): string | undefined {
  const url =
    env.ELAYOAI_CAPACITOR_SERVER_URL?.trim()
    || env.ORGFLOW_CAPACITOR_SERVER_URL?.trim()
    || env.CAPACITOR_SERVER_URL?.trim();

  return url || undefined;
}

export function defaultCapacitorDevServerUrl(): string {
  return "http://localhost:3000";
}
