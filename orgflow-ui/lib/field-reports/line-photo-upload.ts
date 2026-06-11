import { apiFetch } from "@/lib/api/client";
import { isClientUuid } from "@/lib/field-reports/ids";
import {
  parsePhotoIdFromPhotoKey,
  saveLinePhotoLocally,
  type StoredLinePhoto,
} from "@/lib/field-reports/line-photo-store";
import {
  getLocalReport,
  upsertLine,
} from "@/lib/field-reports/repositories/reports-repository";

export type LinePhotoUploadLine = Record<string, unknown> & {
  id?: string;
  has_photo?: boolean;
  photo_ids?: string[];
  photos?: Array<{ id: string; url: string }>;
  photo_url?: string | null;
};

function buildApiErrorMessage(payload: unknown, fallback: string): string {
  const apiPayload = (payload || {}) as {
    error?: { message?: string };
    message?: string;
  };
  return (
    apiPayload.error?.message
    || apiPayload.message
    || fallback
  );
}

function linePhotoFilename(mimeType: string): string {
  return mimeType === "image/png" ? "line-photo.png" : "line-photo.jpg";
}

function toStoredLinePhoto(
  reportId: string,
  lineId: string,
  file: Blob,
  photoId?: string
): StoredLinePhoto {
  const mimeType = file.type || "image/jpeg";
  return {
    lineId: "",
    reportId,
    lineRowId: lineId,
    photoId: photoId || "",
    blob: file,
    mimeType,
    updatedAt: "",
    pendingUpload: true,
  };
}

async function markLinePhotoUploaded(
  reportId: string,
  lineId: string,
  photo: StoredLinePhoto
): Promise<void> {
  await saveLinePhotoLocally(reportId, lineId, photo.blob, {
    pendingUpload: false,
    photoId:
      photo.photoId
      || parsePhotoIdFromPhotoKey(photo.lineId, reportId),
  });
}

async function uploadLinePhotoByClientUuid(
  clientReportUuid: string,
  clientLineUuid: string,
  photo: StoredLinePhoto
): Promise<LinePhotoUploadLine> {
  const formData = new FormData();
  formData.append(
    "file",
    photo.blob,
    linePhotoFilename(photo.mimeType)
  );

  const response = await apiFetch(
    `/field-reports/visits/sync/${clientReportUuid}/lines/${clientLineUuid}/photos`,
    {
      method: "POST",
      headers: {
        "X-Idempotency-Key": clientLineUuid,
      },
      body: formData,
    }
  );

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      buildApiErrorMessage(payload, "העלאת התמונה נכשלה")
    );
  }

  const line = (await response.json()) as LinePhotoUploadLine;
  const reportKey = photo.reportId || clientReportUuid;

  await markLinePhotoUploaded(reportKey, clientLineUuid, photo);

  if (line.id) {
    await upsertLine(clientReportUuid, {
      client_line_uuid: clientLineUuid,
      server_line_id: String(line.id),
    });
  }

  return line;
}

async function uploadLinePhotoToServerReport(
  serverReportId: string,
  lineId: string,
  photo: StoredLinePhoto,
  useLegacySinglePhotoEndpoint: boolean
): Promise<LinePhotoUploadLine> {
  const formData = new FormData();
  formData.append(
    "file",
    photo.blob,
    linePhotoFilename(photo.mimeType)
  );

  const pathSuffix = useLegacySinglePhotoEndpoint ? "photo" : "photos";
  const response = await apiFetch(
    `/field-reports/visits/${serverReportId}/lines/${lineId}/${pathSuffix}`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      buildApiErrorMessage(payload, "העלאת התמונה נכשלה")
    );
  }

  const line = (await response.json()) as LinePhotoUploadLine;
  await markLinePhotoUploaded(serverReportId, lineId, photo);
  return line;
}

/**
 * מעלה תמונת שורה לשרת - מזהה דוח מקומי (UUID) משתמש ב-sync API.
 */
export async function uploadLinePhotoForReport(
  reportId: string,
  lineId: string,
  file: Blob,
  options: {
    photoId?: string;
    /** תמונה ראשונה לשורה בדוח שרת בלבד - endpoint יחיד `/photo`. */
    useLegacySinglePhotoEndpoint?: boolean;
  } = {}
): Promise<LinePhotoUploadLine> {
  const photo = toStoredLinePhoto(reportId, lineId, file, options.photoId);

  if (isClientUuid(reportId)) {
    return uploadLinePhotoByClientUuid(reportId, lineId, photo);
  }

  const local = await getLocalReport(reportId);
  const serverReportId = local?.server_report_id || reportId;

  return uploadLinePhotoToServerReport(
    serverReportId,
    lineId,
    { ...photo, reportId: serverReportId },
    Boolean(options.useLegacySinglePhotoEndpoint)
  );
}

/** מעלה תמונה שמורה מקומית (לסנכרון ממתין). */
export async function uploadStoredLinePhoto(
  photo: StoredLinePhoto
): Promise<LinePhotoUploadLine> {
  const lineId = photo.lineRowId;
  const reportId = photo.reportId;

  if (isClientUuid(reportId)) {
    return uploadLinePhotoByClientUuid(reportId, lineId, photo);
  }

  return uploadLinePhotoToServerReport(reportId, lineId, photo, false);
}
