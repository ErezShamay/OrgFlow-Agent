import { MAX_CHECKLIST_ITEM_PHOTOS } from "@/lib/field-reports/checklist-photo-constants";
import {
  checklistPhotoStorageKey,
  PRIMARY_CHECKLIST_PHOTO_ID,
} from "@/lib/field-reports/checklist-photo-keys";
import type { BlobRecord } from "@/lib/field-reports/db/schema";
import {
  canAddChecklistPhoto as canAddChecklistPhotoBlob,
  countChecklistPhotoBlobs,
  deleteChecklistPhotoBlob,
  getChecklistPhotoBlob,
  listChecklistPhotoBlobsForItem,
  listChecklistPhotoBlobsForReport,
  listPendingChecklistPhotoBlobs,
  saveChecklistPhotoBlob,
} from "@/lib/field-reports/repositories/blobs-repository";

export {
  checklistPhotoStorageKey,
  PRIMARY_CHECKLIST_PHOTO_ID,
  MAX_CHECKLIST_ITEM_PHOTOS,
};

export type StoredChecklistPhoto = {
  storageKey: string;
  reportId: string;
  checklistItemId: string;
  photoId: string;
  blob: Blob;
  mimeType: string;
  updatedAt: string;
  pendingUpload: boolean;
};

function blobRecordToStoredChecklistPhoto(
  record: BlobRecord
): StoredChecklistPhoto {
  const checklistItemId = record.line_id ?? "";
  const photoId = record.photo_id ?? PRIMARY_CHECKLIST_PHOTO_ID;

  return {
    storageKey: checklistPhotoStorageKey(
      record.report_id,
      checklistItemId,
      photoId
    ),
    reportId: record.report_id,
    checklistItemId,
    photoId,
    blob: record.blob,
    mimeType: record.mime_type,
    updatedAt: record.updated_at,
    pendingUpload: record.pending_upload === true,
  };
}

export async function saveChecklistPhotoLocally(
  reportId: string,
  checklistItemId: string,
  file: Blob,
  options: { pendingUpload: boolean; photoId?: string }
): Promise<string> {
  return saveChecklistPhotoBlob(reportId, checklistItemId, file, {
    pendingUpload: options.pendingUpload,
    photoId: options.photoId,
  });
}

export async function loadChecklistPhotoLocally(
  reportId: string,
  checklistItemId: string,
  photoId: string = PRIMARY_CHECKLIST_PHOTO_ID
): Promise<StoredChecklistPhoto | null> {
  const record = await getChecklistPhotoBlob(
    reportId,
    checklistItemId,
    photoId
  );
  return record ? blobRecordToStoredChecklistPhoto(record) : null;
}

export async function listChecklistPhotosForItem(
  reportId: string,
  checklistItemId: string
): Promise<StoredChecklistPhoto[]> {
  const records = await listChecklistPhotoBlobsForItem(reportId, checklistItemId);
  return records.map(blobRecordToStoredChecklistPhoto);
}

export async function listChecklistPhotosForReport(
  reportId: string
): Promise<StoredChecklistPhoto[]> {
  const records = await listChecklistPhotoBlobsForReport(reportId);
  return records.map(blobRecordToStoredChecklistPhoto);
}

export async function listPendingChecklistPhotos(
  reportId?: string
): Promise<StoredChecklistPhoto[]> {
  const records = await listPendingChecklistPhotoBlobs(reportId);
  return records.map(blobRecordToStoredChecklistPhoto);
}

export async function deleteChecklistPhotoLocally(
  reportId: string,
  checklistItemId: string,
  photoId: string = PRIMARY_CHECKLIST_PHOTO_ID
): Promise<void> {
  await deleteChecklistPhotoBlob(reportId, checklistItemId, photoId);
}

export async function countChecklistPhotosLocally(
  reportId: string,
  checklistItemId: string
): Promise<number> {
  return countChecklistPhotoBlobs(reportId, checklistItemId);
}

export function canAddChecklistPhoto(count: number): boolean {
  return canAddChecklistPhotoBlob(count);
}

export function createChecklistPhotoObjectUrl(blob: Blob): string {
  return URL.createObjectURL(blob);
}
