import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));

/** קורא קובץ KEY=VALUE (ללא הרחבת shell). */
export function parseEnvFile(content) {
  const values = {};

  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }

    const eq = line.indexOf("=");
    if (eq <= 0) {
      continue;
    }

    const key = line.slice(0, eq).trim();
    let value = line.slice(eq + 1).trim();

    if (
      (value.startsWith('"') && value.endsWith('"'))
      || (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    values[key] = value;
  }

  return values;
}

/** מחיל משתנים על process.env (לא דורס ערכים קיימים). */
export function applyEnvValues(values, { override = false } = {}) {
  for (const [key, value] of Object.entries(values)) {
    if (override || process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}

/**
 * טוען env לבניית APK - `.env.capacitor.local` → `.env.capacitor` → `.env.local`.
 * FR-034
 */
export function loadCapacitorBuildEnv(options = {}) {
  const uiRoot = options.uiRoot ?? path.join(root, "..");
  const candidates = [
    ".env.capacitor.local",
    ".env.capacitor",
    ".env.local",
  ];

  const loaded = [];

  for (const name of candidates) {
    const filePath = path.join(uiRoot, name);
    if (!fs.existsSync(filePath)) {
      continue;
    }

    const content = fs.readFileSync(filePath, "utf8");
    applyEnvValues(parseEnvFile(content));
    loaded.push(name);
  }

  return { uiRoot, loaded };
}
