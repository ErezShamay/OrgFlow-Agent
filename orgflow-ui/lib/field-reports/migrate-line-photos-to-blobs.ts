import {
  deleteLegacyLinePhotoDatabase,
  readAllLegacyLinePhotos,
  type LegacyStoredLinePhoto,
} from "@/lib/field-reports/legacy-line-photo-indexed-db";
import { photoStorageKey } from "@/lib/field-reports/line-photo-keys";
import {
  getLinePhotoBlob,
  PRIMARY_LINE_PHOTO_ID,
  saveLinePhotoBlob,
} from "@/lib/field-reports/repositories/blobs-repository";

import { ELAYOAI_FIELD_REPORTS_LINE_PHOTOS_MIGRATED_KEY } from "@/lib/elayoai/keys";

const MIGRATION_MARKER_KEY = ELAYOAI_FIELD_REPORTS_LINE_PHOTOS_MIGRATED_KEY;

let migrationPromise: Promise<void> | null = null;

function isMigrationMarkedComplete(): boolean {
  if (typeof localStorage === "undefined") {
    return false;
  }
  return localStorage.getItem(MIGRATION_MARKER_KEY) === "1";
}

function markMigrationComplete(): void {
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(MIGRATION_MARKER_KEY, "1");
  }
}

function normalizeLegacyPhoto(
  record: LegacyStoredLinePhoto
): LegacyStoredLinePhoto {
  const photoId = record.photoId || PRIMARY_LINE_PHOTO_ID;
  const lineRowId =
    record.lineRowId
    || parseLineRowIdFromLegacyKey(record.lineId, record.reportId);
  return {
    ...record,
    photoId,
    lineRowId,
    lineId: photoStorageKey(record.reportId, lineRowId, photoId),
  };
}

function parseLineRowIdFromLegacyKey(lineKey: string, reportId: string) {
  const prefix = `${reportId}:`;
  if (!lineKey.startsWith(prefix)) {
    return lineKey;
  }
  const remainder = lineKey.slice(prefix.length);
  const parts = remainder.split(":");
  return parts[0] ?? remainder;
}

async function migrateLegacyRecord(
  record: LegacyStoredLinePhoto
): Promise<void> {
  const normalized = normalizeLegacyPhoto(record);
  const existing = await getLinePhotoBlob(
    normalized.reportId,
    normalized.lineRowId,
    normalized.photoId
  );

  if (existing) {
    return;
  }

  await saveLinePhotoBlob(
    normalized.reportId,
    normalized.lineRowId,
    normalized.blob,
    {
      pendingUpload: normalized.pendingUpload,
      photoId: normalized.photoId,
    }
  );
}

/**
 * מעביר תמונות מ-`orgflow-field-report-line-photos` ל-store `blobs` המאוחד.
 * חד-פעמי: מסומן ב-localStorage; אם אין נתונים ישנים - מסמן וממשיך.
 */
export async function migrateLinePhotosFromLegacyIndexedDb(): Promise<void> {
  if (isMigrationMarkedComplete()) {
    return;
  }

  let legacyRecords: LegacyStoredLinePhoto[] = [];
  try {
    legacyRecords = await readAllLegacyLinePhotos();
  } catch {
    markMigrationComplete();
    return;
  }

  if (legacyRecords.length === 0) {
    await deleteLegacyLinePhotoDatabase().catch(() => undefined);
    markMigrationComplete();
    return;
  }

  for (const record of legacyRecords) {
    await migrateLegacyRecord(record);
  }

  await deleteLegacyLinePhotoDatabase();
  markMigrationComplete();
}

/** מבטיח שמיגרציה הושלמה לפני קריאה/כתיבה דרך `line-photo-store`. */
export async function ensureLinePhotosMigratedToBlobs(): Promise<void> {
  if (!migrationPromise) {
    migrationPromise = migrateLinePhotosFromLegacyIndexedDb().catch((error) => {
      migrationPromise = null;
      throw error;
    });
  }
  await migrationPromise;
}

/** לבדיקות - מאפס סימון מיגרציה. */
export function resetLinePhotoMigrationMarkerForTests(): void {
  if (typeof localStorage !== "undefined") {
    localStorage.removeItem(MIGRATION_MARKER_KEY);
  }
  migrationPromise = null;
}
