/** קודי שגיאה מובנים מ-@capacitor/camera 8.1+ (native). */
export const CAPACITOR_CAMERA_CANCELLED_CODE = "OS-PLUG-CAMR-0006";

export type CapacitorCameraErrorLike = {
  code?: string;
  message?: string;
};

export function isCapacitorCameraError(
  err: unknown
): err is CapacitorCameraErrorLike {
  return (
    typeof err === "object"
    && err !== null
    && ("code" in err || "message" in err)
  );
}

/** המשתמש ביטל את המצלמה / הגלריה - לא שגיאת אפליקציה. */
export function isCapacitorCameraUserCancelled(err: unknown): boolean {
  if (!isCapacitorCameraError(err)) {
    return false;
  }

  if (err.code === CAPACITOR_CAMERA_CANCELLED_CODE) {
    return true;
  }

  const message = (err.message ?? "").toLowerCase();
  return (
    message.includes("cancel")
    || message.includes("cancelled")
    || message.includes("canceled")
  );
}

export function getCapacitorCameraErrorCode(err: unknown): string | undefined {
  return isCapacitorCameraError(err) ? err.code : undefined;
}
