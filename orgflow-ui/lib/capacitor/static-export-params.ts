import { capacitorStaticExportParams } from "@/lib/capacitor/build-mode";

function isExplicitCapacitorStaticExportBuild(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return (
    env.ELAYOAI_CAPACITOR_BUILD === "static"
    || env.ORGFLOW_CAPACITOR_BUILD === "static"
    || env.ELAYOAI_CAPACITOR_BUILD_MODE === "static"
    || env.ORGFLOW_CAPACITOR_BUILD_MODE === "static"
  );
}

/**
 * Placeholder `/_` routes — רק ל-`npm run build:mobile` (ELAYOAI_CAPACITOR_BUILD=static).
 * ב-Vercel / `npm run build` רגיל מחזירים [] (דינמי ב-runtime).
 */
export function dashboardDynamicSegmentParams(
  env: NodeJS.ProcessEnv = process.env,
): Array<{ id: string }> {
  if (env.VERCEL === "1") {
    return [];
  }

  if (!isExplicitCapacitorStaticExportBuild(env)) {
    return [];
  }

  return capacitorStaticExportParams();
}
