#!/usr/bin/env node
/**
 * Next.js static export ל-APK - טוען `.env.capacitor.local` לפני build (FR-034).
 */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loadCapacitorBuildEnv } from "./load-capacitor-env.mjs";

const uiRoot = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  ".."
);

const { loaded } = loadCapacitorBuildEnv({ uiRoot });

if (loaded.length > 0) {
  console.log(`[build:mobile] Env: ${loaded.join(", ")}`);
} else {
  console.warn(
    "[build:mobile] No .env.capacitor.local - copy .env.capacitor.example (NEXT_PUBLIC_API_URL, Supabase)"
  );
}

if (!process.env.NEXT_PUBLIC_API_URL) {
  console.warn(
    "[build:mobile] NEXT_PUBLIC_API_URL missing - APK will use http://localhost:3000 (לא יעבוד על מכשיר)"
  );
}

if (
  !process.env.NEXT_PUBLIC_SUPABASE_URL
  || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
) {
  console.warn(
    "[build:mobile] Supabase env missing - login will fail in APK"
  );
}

const result = spawnSync(
  "npx",
  ["next", "build"],
  {
    cwd: uiRoot,
    env: {
      ...process.env,
      ELAYOAI_CAPACITOR_BUILD: "static",
      ELAYOAI_CAPACITOR_BUILD_MODE: "static",
    },
    stdio: "inherit",
    shell: process.platform === "win32",
  }
);

process.exit(result.status ?? 1);
