import { deleteDB, openDB, type IDBPDatabase } from "idb";

import { migrateElayoAiPersistence } from "@/lib/elayoai/migrate-storage";
import {
  FIELD_REPORT_DB_NAME,
  FIELD_REPORT_DB_VERSION,
  FIELD_REPORT_STORES,
  type FieldReportDBSchema,
} from "@/lib/field-reports/db/schema";

let dbPromise: Promise<IDBPDatabase<FieldReportDBSchema>> | null = null;

export function isFieldReportIndexedDbAvailable(): boolean {
  return typeof indexedDB !== "undefined";
}

function upgradeFieldReportDatabase(
  db: IDBPDatabase<FieldReportDBSchema>
) {
  if (!db.objectStoreNames.contains(FIELD_REPORT_STORES.catalog)) {
    db.createObjectStore(FIELD_REPORT_STORES.catalog, {
      keyPath: "organization_id",
    });
  }

  if (!db.objectStoreNames.contains(FIELD_REPORT_STORES.reports)) {
    const reports = db.createObjectStore(FIELD_REPORT_STORES.reports, {
      keyPath: "client_report_uuid",
    });
    reports.createIndex("by-organization", "organization_id");
    reports.createIndex("by-server-id", "server_report_id");
  }

  if (!db.objectStoreNames.contains(FIELD_REPORT_STORES.blobs)) {
    const blobs = db.createObjectStore(FIELD_REPORT_STORES.blobs, {
      keyPath: "id",
    });
    blobs.createIndex("by-report", "report_id");
    blobs.createIndex("by-report-line", "report_line_key");
  }

  if (!db.objectStoreNames.contains(FIELD_REPORT_STORES.sync_queue)) {
    const syncQueue = db.createObjectStore(FIELD_REPORT_STORES.sync_queue, {
      keyPath: "client_report_uuid",
    });
    syncQueue.createIndex("by-organization", "organization_id");
  }

  if (!db.objectStoreNames.contains(FIELD_REPORT_STORES.open_issues)) {
    db.createObjectStore(FIELD_REPORT_STORES.open_issues, {
      keyPath: "organization_id",
    });
  }
}

/**
 * פותח את מסד הדוחות (או מחזיר מופע קיים מהמטמון).
 * Repositories (FR-002+) ישתמשו ב-`getFieldReportDatabase()`.
 */
export async function openFieldReportDatabase(): Promise<
  IDBPDatabase<FieldReportDBSchema>
> {
  if (!isFieldReportIndexedDbAvailable()) {
    throw new Error("IndexedDB is not available");
  }

  return openDB<FieldReportDBSchema>(
    FIELD_REPORT_DB_NAME,
    FIELD_REPORT_DB_VERSION,
    {
      upgrade(database) {
        upgradeFieldReportDatabase(database);
      },
    }
  );
}

export function getFieldReportDatabase(): Promise<
  IDBPDatabase<FieldReportDBSchema>
> {
  if (!dbPromise) {
    dbPromise = migrateElayoAiPersistence().then(() =>
      openFieldReportDatabase()
    );
  }
  return dbPromise;
}

/** מאפס מטמון חיבור (בדיקות / מחיקת DB). */
export function resetFieldReportDatabaseConnection() {
  dbPromise = null;
}

export async function closeFieldReportDatabase(): Promise<void> {
  if (!dbPromise) {
    return;
  }

  const database = await dbPromise;
  database.close();
  dbPromise = null;
}

/** מוחק את מסד הדוחות - לשימוש בבדיקות (FR-008) בלבד. */
export async function deleteFieldReportDatabase(): Promise<void> {
  await closeFieldReportDatabase();
  await deleteDB(FIELD_REPORT_DB_NAME);
  resetFieldReportDatabaseConnection();
}
