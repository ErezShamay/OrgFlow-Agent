import { MAX_LINE_PHOTOS } from "@/lib/field-reports/line-photo-constants";
import {
  blobStorageKey,
  FIELD_REPORT_STORES,
  reportLineIndexKey,
  type BlobRecord,
} from "@/lib/field-reports/db/schema";
import { getFieldReportDatabase } from "@/lib/field-reports/db/field-report-db";
import { PRIMARY_LINE_PHOTO_ID } from "@/lib/field-reports/line-photo-keys";

export { PRIMARY_LINE_PHOTO_ID };

export type { BlobRecord };

export type SaveLinePhotoOptions = {
  pendingUpload: boolean;
  photoId?: string;
};

export type StoredReportPdf = {
  reportId: string;
  blob: Blob;
  filename: string;
  generatedAt: string;
};

function nowIso() {
  return new Date().toISOString();
}

function newPhotoId(): string {
  if (
    typeof globalThis.crypto !== "undefined"
    && typeof globalThis.crypto.randomUUID === "function"
  ) {
    return globalThis.crypto.randomUUID();
  }

  return `photo-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function putBlobRecord(record: BlobRecord): Promise<void> {
  const database = await getFieldReportDatabase();
  await database.put(FIELD_REPORT_STORES.blobs, record);
}

async function getBlobRecord(id: string): Promise<BlobRecord | null> {
  const database = await getFieldReportDatabase();
  const record = await database.get(FIELD_REPORT_STORES.blobs, id);
  return record ?? null;
}

async function listBlobsForReport(reportId: string): Promise<BlobRecord[]> {
  const database = await getFieldReportDatabase();
  return database.getAllFromIndex(
    FIELD_REPORT_STORES.blobs,
    "by-report",
    reportId
  );
}

function isLinePhoto(record: BlobRecord): boolean {
  return record.kind === "line_photo";
}

/**
 * שומר תמונת שורה - `reportId` / `lineId` הם מזהי קליינט (או שרת לתאימות).
 */
export async function saveLinePhotoBlob(
  reportId: string,
  lineId: string,
  file: Blob,
  options: SaveLinePhotoOptions
): Promise<string> {
  const photoId = options.photoId ?? newPhotoId();
  const record: BlobRecord = {
    id: blobStorageKey(reportId, "line_photo", { lineId, photoId }),
    kind: "line_photo",
    report_id: reportId,
    report_line_key: reportLineIndexKey(reportId, lineId),
    line_id: lineId,
    photo_id: photoId,
    blob: file,
    mime_type: file.type || "image/jpeg",
    updated_at: nowIso(),
    pending_upload: options.pendingUpload,
  };

  await putBlobRecord(record);
  return photoId;
}

export async function getLinePhotoBlob(
  reportId: string,
  lineId: string,
  photoId: string = PRIMARY_LINE_PHOTO_ID
): Promise<BlobRecord | null> {
  return getBlobRecord(
    blobStorageKey(reportId, "line_photo", { lineId, photoId })
  );
}

export async function listLinePhotoBlobsForReport(
  reportId: string
): Promise<BlobRecord[]> {
  const records = await listBlobsForReport(reportId);
  return records
    .filter(isLinePhoto)
    .sort((left, right) => left.updated_at.localeCompare(right.updated_at));
}

export async function listLinePhotoBlobsForLine(
  reportId: string,
  lineId: string
): Promise<BlobRecord[]> {
  const database = await getFieldReportDatabase();
  const records = await database.getAllFromIndex(
    FIELD_REPORT_STORES.blobs,
    "by-report-line",
    reportLineIndexKey(reportId, lineId)
  );

  return records
    .filter(isLinePhoto)
    .sort((left, right) => left.updated_at.localeCompare(right.updated_at));
}

export async function listPendingLinePhotoBlobs(
  reportId?: string
): Promise<BlobRecord[]> {
  const database = await getFieldReportDatabase();
  const records = reportId
    ? await listBlobsForReport(reportId)
    : await database.getAll(FIELD_REPORT_STORES.blobs);

  return records.filter(
    (record) => isLinePhoto(record) && record.pending_upload === true
  );
}

export async function deleteLinePhotoBlob(
  reportId: string,
  lineId: string,
  photoId: string = PRIMARY_LINE_PHOTO_ID
): Promise<void> {
  const database = await getFieldReportDatabase();
  await database.delete(
    FIELD_REPORT_STORES.blobs,
    blobStorageKey(reportId, "line_photo", { lineId, photoId })
  );
}

export async function countLinePhotoBlobs(
  reportId: string,
  lineId: string
): Promise<number> {
  const photos = await listLinePhotoBlobsForLine(reportId, lineId);
  return photos.length;
}

export function canAddLinePhoto(count: number): boolean {
  return count < MAX_LINE_PHOTOS;
}

export async function saveReportPdfBlob(
  reportId: string,
  blob: Blob,
  filename: string,
  generatedAt: Date = new Date()
): Promise<void> {
  const record: BlobRecord = {
    id: blobStorageKey(reportId, "pdf"),
    kind: "pdf",
    report_id: reportId,
    report_line_key: null,
    line_id: null,
    photo_id: null,
    blob,
    mime_type: blob.type || "application/pdf",
    filename,
    updated_at: generatedAt.toISOString(),
    pending_upload: false,
  };

  await putBlobRecord(record);
}

export async function getReportPdfBlob(
  reportId: string
): Promise<StoredReportPdf | null> {
  const record = await getBlobRecord(blobStorageKey(reportId, "pdf"));
  if (!record || record.kind !== "pdf") {
    return null;
  }

  return {
    reportId: record.report_id,
    blob: record.blob,
    filename: record.filename || `${reportId}.pdf`,
    generatedAt: record.updated_at,
  };
}

export async function hasReportPdfBlob(reportId: string): Promise<boolean> {
  const record = await getReportPdfBlob(reportId);
  return Boolean(record?.blob);
}

export async function deleteReportPdfBlob(reportId: string): Promise<void> {
  const database = await getFieldReportDatabase();
  await database.delete(
    FIELD_REPORT_STORES.blobs,
    blobStorageKey(reportId, "pdf")
  );
}

/** מוחק את כל ה-blobs של דוח (תמונות + PDF). */
export async function deleteAllBlobsForReport(
  reportId: string
): Promise<void> {
  const records = await listBlobsForReport(reportId);
  const database = await getFieldReportDatabase();
  const transaction = database.transaction(
    FIELD_REPORT_STORES.blobs,
    "readwrite"
  );

  await Promise.all(
    records.map((record) => transaction.store.delete(record.id))
  );
  await transaction.done;
}
