#!/usr/bin/env node
/**
 * בניית APK לדוחות שטח (FR-034).
 *
 * שימוש:
 *   node scripts/build-android-apk.mjs debug
 *   node scripts/build-android-apk.mjs release
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loadCapacitorBuildEnv } from "./load-capacitor-env.mjs";
import { resolveAndroidBuildEnv } from "./resolve-android-build-env.mjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const uiRoot = path.join(scriptDir, "..");
const androidRoot = path.join(uiRoot, "android");

const variant = (process.argv[2] || "debug").toLowerCase();

if (variant !== "debug" && variant !== "release") {
  console.error("Usage: node scripts/build-android-apk.mjs [debug|release]");
  process.exit(1);
}

const { loaded } = loadCapacitorBuildEnv({ uiRoot });

const { env: androidBuildEnv, notes: androidEnvNotes, javaHome } =
  resolveAndroidBuildEnv(process.env);

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd ?? uiRoot,
    env: { ...androidBuildEnv, ...options.env },
    stdio: "inherit",
    shell: process.platform === "win32",
  });

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

console.log("ElayoAI - Android APK build");
console.log(`Variant: ${variant}`);
for (const note of androidEnvNotes) {
  console.log(note);
}
if (!javaHome) {
  console.error(
    "\nCannot build APK without Java 21. On macOS: brew install openjdk@21"
  );
  process.exit(1);
}
if (loaded.length > 0) {
  console.log(`Env files: ${loaded.join(", ")}`);
} else {
  console.warn(
    "No .env.capacitor.local - copy .env.capacitor.example and set NEXT_PUBLIC_API_URL"
  );
}

if (!process.env.NEXT_PUBLIC_API_URL && variant === "release") {
  console.warn(
    "WARNING: NEXT_PUBLIC_API_URL is not set; the APK will default to http://localhost:3000"
  );
}

const keystoreFile = path.join(androidRoot, "keystore.properties");
if (variant === "release" && !fs.existsSync(keystoreFile)) {
  console.error(
    "Release build requires android/keystore.properties (see keystore.properties.example)"
  );
  process.exit(1);
}

console.log("\n[0/4] Launcher icons + splash screens from brand SVG...");
run("node", ["scripts/generate-android-icons.mjs"]);

console.log("\n[1/4] Next.js static export (Build B)...");
run("node", ["scripts/build-mobile-export.mjs"]);

console.log("\n[2/4] cap sync android...");
run("npx", ["cap", "sync", "android"]);

const gradleTask =
  variant === "release" ? "assembleRelease" : "assembleDebug";
const gradlew =
  process.platform === "win32" ? "gradlew.bat" : "./gradlew";

console.log(`\n[3/4] Gradle ${gradleTask}...`);
run(gradlew, [gradleTask], {
  cwd: androidRoot,
  env: {
    ELAYOAI_ANDROID_VERSION_CODE:
      process.env.ELAYOAI_ANDROID_VERSION_CODE
      || process.env.ORGFLOW_ANDROID_VERSION_CODE
      || "1",
    ELAYOAI_ANDROID_VERSION_NAME:
      process.env.ELAYOAI_ANDROID_VERSION_NAME
      || process.env.ORGFLOW_ANDROID_VERSION_NAME
      || "1.0.0",
  },
});

const apkSubdir = variant === "release" ? "release" : "debug";
const apkName =
  variant === "release"
    ? "app-release.apk"
    : "app-debug.apk";
const apkPath = path.join(
  androidRoot,
  "app",
  "build",
  "outputs",
  "apk",
  apkSubdir,
  apkName
);

console.log("\nDone.");
if (fs.existsSync(apkPath)) {
  console.log(`APK: ${apkPath}`);
} else {
  console.log(`Look under: ${path.join(androidRoot, "app", "build", "outputs", "apk")}`);
}
