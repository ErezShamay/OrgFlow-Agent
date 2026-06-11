import { openDB, type IDBPDatabase } from "idb";

import {
  ELAYOAI_FIELD_REPORT_DB_NAME,
  LEGACY_ORGFLOW_FIELD_REPORT_DB_NAME,
} from "@/lib/elayoai/keys";
import {
  FIELD_REPORT_DB_VERSION,
  FIELD_REPORT_STORES,
  type FieldReportDBSchema,
} from "@/lib/field-reports/db/schema";

async function databaseExists(name: string): Promise<boolean> {
  if (typeof indexedDB === "undefined") {
    return false;
  }

  if (typeof indexedDB.databases === "function") {
    const databases = await indexedDB.databases();
    return databases.some((entry) => entry.name === name);
  }

  return new Promise((resolve) => {
    const request = indexedDB.open(name);
    request.onsuccess = () => {
      request.result.close();
      resolve(true);
    };
    request.onerror = () => resolve(false);
  });
}

async function copyObjectStore(
  source: IDBPDatabase<FieldReportDBSchema>,
  target: IDBPDatabase<FieldReportDBSchema>,
  storeName: (typeof FIELD_REPORT_STORES)[keyof typeof FIELD_REPORT_STORES]
) {
  if (
    !source.objectStoreNames.contains(storeName)
    || !target.objectStoreNames.contains(storeName)
  ) {
    return;
  }

  const records = await source.getAll(storeName);
  if (records.length === 0) {
    return;
  }

  const transaction = target.transaction(storeName, "readwrite");
  for (const record of records) {
    await transaction.store.put(record);
  }

  await transaction.done;
}

/** מעתיק נתונים מ-`orgflow-field-reports` ל-`elayoai-field-reports`. */
export async function migrateLegacyFieldReportDatabase(): Promise<void> {
  if (typeof indexedDB === "undefined") {
    return;
  }

  const hasLegacy = await databaseExists(LEGACY_ORGFLOW_FIELD_REPORT_DB_NAME);
  if (!hasLegacy) {
    return;
  }

  const hasTarget = await databaseExists(ELAYOAI_FIELD_REPORT_DB_NAME);

  const legacy = await openDB<FieldReportDBSchema>(
    LEGACY_ORGFLOW_FIELD_REPORT_DB_NAME
  );

  if (!hasTarget) {
    await openDB<FieldReportDBSchema>(
      ELAYOAI_FIELD_REPORT_DB_NAME,
      FIELD_REPORT_DB_VERSION,
      {
        upgrade(database) {
          for (const storeName of Object.values(FIELD_REPORT_STORES)) {
            if (storeName === FIELD_REPORT_STORES.catalog) {
              if (!database.objectStoreNames.contains(storeName)) {
                database.createObjectStore(storeName, {
                  keyPath: "organization_id",
                });
              }
              continue;
            }

            if (storeName === FIELD_REPORT_STORES.reports) {
              if (!database.objectStoreNames.contains(storeName)) {
                const reports = database.createObjectStore(storeName, {
                  keyPath: "client_report_uuid",
                });
                reports.createIndex("by-organization", "organization_id");
                reports.createIndex("by-server-id", "server_report_id");
              }
              continue;
            }

            if (storeName === FIELD_REPORT_STORES.blobs) {
              if (!database.objectStoreNames.contains(storeName)) {
                const blobs = database.createObjectStore(storeName, {
                  keyPath: "id",
                });
                blobs.createIndex("by-report", "report_id");
                blobs.createIndex("by-report-line", "report_line_key");
              }
              continue;
            }

            if (storeName === FIELD_REPORT_STORES.sync_queue) {
              if (!database.objectStoreNames.contains(storeName)) {
                const syncQueue = database.createObjectStore(storeName, {
                  keyPath: "client_report_uuid",
                });
                syncQueue.createIndex("by-organization", "organization_id");
              }
              continue;
            }

            if (storeName === FIELD_REPORT_STORES.open_issues) {
              if (!database.objectStoreNames.contains(storeName)) {
                database.createObjectStore(storeName, {
                  keyPath: "organization_id",
                });
              }
            }
          }
        },
      }
    );
  }

  const target = await openDB<FieldReportDBSchema>(ELAYOAI_FIELD_REPORT_DB_NAME);

  for (const storeName of Object.values(FIELD_REPORT_STORES)) {
    await copyObjectStore(legacy, target, storeName);
  }

  legacy.close();
  target.close();
}
