/** מזהה תמונה מקומית ראשית - תואם גרסאות 1–2 של line-photo-store. */
export const PRIMARY_LINE_PHOTO_ID = "primary";

/** מפתח אחסון legacy (`reportId:lineId:photoId`) - לתאימות sync ו-parse. */
export function photoStorageKey(
  reportId: string,
  lineId: string,
  photoId: string
) {
  return `${reportId}:${lineId}:${photoId}`;
}

export function parseLineIdFromPhotoKey(lineKey: string, reportId: string) {
  const prefix = `${reportId}:`;
  if (!lineKey.startsWith(prefix)) {
    return lineKey;
  }
  const remainder = lineKey.slice(prefix.length);
  const parts = remainder.split(":");
  return parts[0] ?? remainder;
}

export function parsePhotoIdFromPhotoKey(lineKey: string, reportId: string) {
  const prefix = `${reportId}:`;
  if (!lineKey.startsWith(prefix)) {
    return PRIMARY_LINE_PHOTO_ID;
  }
  const remainder = lineKey.slice(prefix.length);
  const parts = remainder.split(":");
  return parts[1] ?? PRIMARY_LINE_PHOTO_ID;
}
