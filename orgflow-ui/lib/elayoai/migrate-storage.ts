import {
  ELAYOAI_ACCESS_TOKEN_KEY,
  ELAYOAI_FIELD_REPORT_DB_MIGRATED_MARKER,
  ELAYOAI_LOCALE_KEY,
  ELAYOAI_ORG_ID_KEY,
  ELAYOAI_THEME_KEY,
  LEGACY_ORGFLOW_ACCESS_TOKEN_KEY,
  LEGACY_ORGFLOW_LOCALE_KEY,
  LEGACY_ORGFLOW_ORG_ID_KEY,
  LEGACY_ORGFLOW_THEME_KEY,
} from "@/lib/elayoai/keys";
import { migrateLegacyFieldReportDatabase } from "@/lib/elayoai/migrate-field-report-db";

function copyStorageValue(
  storage: Storage,
  fromKey: string,
  toKey: string
) {
  const value = storage.getItem(fromKey);
  if (value === null || storage.getItem(toKey) !== null) {
    return;
  }

  storage.setItem(toKey, value);
}

function migratePrefixedKeys(storage: Storage, fromPrefix: string, toPrefix: string) {
  const keys: string[] = [];

  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    if (key?.startsWith(fromPrefix)) {
      keys.push(key);
    }
  }

  for (const key of keys) {
    const suffix = key.slice(fromPrefix.length);
    copyStorageValue(storage, key, `${toPrefix}${suffix}`);
  }
}

function migrateOrgflowPrefixedLocalStorage() {
  if (typeof window === "undefined") {
    return;
  }

  migratePrefixedKeys(localStorage, "orgflow-field-reports", "elayoai-field-reports");
  migratePrefixedKeys(localStorage, "orgflow-field-report", "elayoai-field-report");
  migratePrefixedKeys(
    localStorage,
    "orgflow-field-reports-send-queue",
    "elayoai-field-reports-send-queue"
  );
}

/** מעתיק מפתחות OrgFlow ל-ElayoAI (פעם אחת לכל דפדפן / WebView). */
export function migrateElayoAiStorage(): void {
  if (typeof window === "undefined") {
    return;
  }

  copyStorageValue(localStorage, LEGACY_ORGFLOW_THEME_KEY, ELAYOAI_THEME_KEY);
  copyStorageValue(localStorage, LEGACY_ORGFLOW_LOCALE_KEY, ELAYOAI_LOCALE_KEY);
  copyStorageValue(
    sessionStorage,
    LEGACY_ORGFLOW_ACCESS_TOKEN_KEY,
    ELAYOAI_ACCESS_TOKEN_KEY
  );
  copyStorageValue(sessionStorage, LEGACY_ORGFLOW_ORG_ID_KEY, ELAYOAI_ORG_ID_KEY);
  migrateOrgflowPrefixedLocalStorage();
}

/** מיגרציית IndexedDB + localStorage - לפני שימוש בדוחות שטח. */
export async function migrateElayoAiPersistence(): Promise<void> {
  migrateElayoAiStorage();

  if (typeof window === "undefined") {
    return;
  }

  if (localStorage.getItem(ELAYOAI_FIELD_REPORT_DB_MIGRATED_MARKER) === "1") {
    return;
  }

  await migrateLegacyFieldReportDatabase();
  localStorage.setItem(ELAYOAI_FIELD_REPORT_DB_MIGRATED_MARKER, "1");
}
