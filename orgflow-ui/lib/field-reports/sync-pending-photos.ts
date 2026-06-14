import {
  syncAllPendingLinePhotos,
  syncPendingLinePhotosForReport,
  type LinePhotoSyncResult,
} from "@/lib/field-reports/sync-pending-line-photos";
import { listPendingChecklistPhotos } from "@/lib/field-reports/checklist-photo-store";

export type PendingPhotosSyncResult = LinePhotoSyncResult & {
  checklist_pending: number;
};

/** סנכרון תמונות שורות + ספירת תמונות צ'קליסט ממתינות (§12, §13.2). */
export async function syncPendingPhotosForReport(
  reportId: string
): Promise<PendingPhotosSyncResult> {
  const lineResult = await syncPendingLinePhotosForReport(reportId);
  const checklistPending = await listPendingChecklistPhotos(reportId);

  return {
    ...lineResult,
    checklist_pending: checklistPending.length,
  };
}

export async function syncAllPendingPhotos(): Promise<PendingPhotosSyncResult> {
  const lineResult = await syncAllPendingLinePhotos();
  const checklistPending = await listPendingChecklistPhotos();

  return {
    ...lineResult,
    checklist_pending: checklistPending.length,
  };
}

export {
  syncPendingLinePhotosForReport,
  syncAllPendingLinePhotos,
};
