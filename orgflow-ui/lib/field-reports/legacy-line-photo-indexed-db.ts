import { LEGACY_ORGFLOW_FIELD_REPORT_LINE_PHOTOS_DB } from "@/lib/elayoai/keys";

/** מסד IndexedDB ישן - לפני איחוד ל-`elayoai-field-reports` (FR-007). */
export const LEGACY_LINE_PHOTO_DB_NAME =
  LEGACY_ORGFLOW_FIELD_REPORT_LINE_PHOTOS_DB;
export const LEGACY_LINE_PHOTO_DB_VERSION = 2;
export const LEGACY_LINE_PHOTO_STORE_NAME = "photos";

export type LegacyStoredLinePhoto = {
  lineId: string;
  reportId: string;
  lineRowId: string;
  photoId: string;
  blob: Blob;
  mimeType: string;
  updatedAt: string;
  pendingUpload: boolean;
};

function openLegacyDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("IndexedDB is not available"));
      return;
    }

    const request = indexedDB.open(
      LEGACY_LINE_PHOTO_DB_NAME,
      LEGACY_LINE_PHOTO_DB_VERSION
    );

    request.onerror = () => {
      reject(request.error ?? new Error("Failed to open legacy photo store"));
    };

    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(LEGACY_LINE_PHOTO_STORE_NAME)) {
        database.createObjectStore(LEGACY_LINE_PHOTO_STORE_NAME, {
          keyPath: "lineId",
        });
      }
    };

    request.onsuccess = () => {
      resolve(request.result);
    };
  });
}

/** קורא את כל התמונות מה-store הישן (למיגרציה חד-פעמית). */
export async function readAllLegacyLinePhotos(): Promise<LegacyStoredLinePhoto[]> {
  const database = await openLegacyDatabase();

  const records = await new Promise<LegacyStoredLinePhoto[]>((resolve, reject) => {
    const transaction = database.transaction(
      LEGACY_LINE_PHOTO_STORE_NAME,
      "readonly"
    );
    const store = transaction.objectStore(LEGACY_LINE_PHOTO_STORE_NAME);
    const request = store.getAll();

    request.onerror = () => {
      reject(request.error ?? new Error("Failed to read legacy line photos"));
    };
    request.onsuccess = () => {
      resolve((request.result as LegacyStoredLinePhoto[]) ?? []);
    };
  });

  database.close();
  return records;
}

/** כותב רשומה ל-store הישן - לבדיקות מיגרציה (FR-007). */
export async function writeLegacyLinePhotoForTests(
  record: LegacyStoredLinePhoto
): Promise<void> {
  const database = await openLegacyDatabase();

  await new Promise<void>((resolve, reject) => {
    const transaction = database.transaction(
      LEGACY_LINE_PHOTO_STORE_NAME,
      "readwrite"
    );
    const store = transaction.objectStore(LEGACY_LINE_PHOTO_STORE_NAME);
    const request = store.put(record);

    request.onerror = () => {
      reject(request.error ?? new Error("Failed to write legacy line photo"));
    };
    request.onsuccess = () => {
      resolve();
    };
  });

  database.close();
}

/** מוחד את מסד התמונות הישן אחרי מיגרציה מוצלחת. */
export async function deleteLegacyLinePhotoDatabase(): Promise<void> {
  if (typeof indexedDB === "undefined") {
    return;
  }

  await new Promise<void>((resolve, reject) => {
    const request = indexedDB.deleteDatabase(LEGACY_LINE_PHOTO_DB_NAME);
    request.onerror = () => {
      reject(request.error ?? new Error("Failed to delete legacy photo database"));
    };
    request.onblocked = () => {
      resolve();
    };
    request.onsuccess = () => {
      resolve();
    };
  });
}
