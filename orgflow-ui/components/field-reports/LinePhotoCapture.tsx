"use client";

import { useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import {
  createLinePhotoObjectUrl,
  deleteLinePhotoLocally,
  loadLinePhotoLocally,
  saveLinePhotoLocally,
} from "@/lib/field-reports/line-photo-store";
import { FR_TOUCH_BUTTON } from "@/lib/field-reports/touch-input-class";
import { useOffline } from "@/providers/OfflineProvider";

type LinePhotoCaptureProps = {
  reportId: string;
  lineId: string;
  hasServerPhoto: boolean;
  photoUrl?: string | null;
  disabled?: boolean;
  onPhotoChange?: (hasPhoto: boolean) => void;
};

export default function LinePhotoCapture({
  reportId,
  lineId,
  hasServerPhoto,
  photoUrl,
  disabled = false,
  onPhotoChange,
}: LinePhotoCaptureProps) {
  const { isOnline } = useOffline();
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [pendingLocal, setPendingLocal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [cameraBlocked, setCameraBlocked] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    async function loadPreview() {
      setError("");

      if (hasServerPhoto && photoUrl && isOnline) {
        const response = await apiFetch(photoUrl);
        if (!response.ok) {
          return;
        }
        const blob = await response.blob();
        if (cancelled) {
          return;
        }
        objectUrl = createLinePhotoObjectUrl(blob);
        setPreviewUrl(objectUrl);
        setPendingLocal(false);
        return;
      }

      const local = await loadLinePhotoLocally(reportId, lineId);
      if (cancelled || !local) {
        if (!cancelled && !hasServerPhoto) {
          setPreviewUrl(null);
          setPendingLocal(false);
        }
        return;
      }

      objectUrl = createLinePhotoObjectUrl(local.blob);
      setPreviewUrl(objectUrl);
      setPendingLocal(local.pendingUpload);
    }

    void loadPreview();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [hasServerPhoto, photoUrl, isOnline, lineId, reportId]);

  useEffect(() => {
    return () => {
      if (previewUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  async function handleFileSelected(file: File | null) {
    if (!file || disabled) {
      return;
    }

    setError("");
    setCameraBlocked(false);
    setUploading(true);

    try {
      await saveLinePhotoLocally(reportId, lineId, file, {
        pendingUpload: !isOnline,
      });

      if (previewUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(previewUrl);
      }
      setPreviewUrl(createLinePhotoObjectUrl(file));
      setPendingLocal(!isOnline);
      onPhotoChange?.(true);

      if (isOnline) {
        try {
          const formData = new FormData();
          formData.append("file", file, file.name || "line-photo.jpg");

          const response = await apiFetch(
            `/field-reports/visits/${reportId}/lines/${lineId}/photo`,
            {
              method: "POST",
              body: formData,
            }
          );

          if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(
              payload.error?.message
                || payload.message
                || "העלאת התמונה נכשלה"
            );
          }

          await saveLinePhotoLocally(reportId, lineId, file, {
            pendingUpload: false,
          });
          setPendingLocal(false);
        } catch (uploadError: unknown) {
          // Keep the local photo as pending so background sync can retry.
          await saveLinePhotoLocally(reportId, lineId, file, {
            pendingUpload: true,
          });
          setPendingLocal(true);
          setError(getPhotoActionErrorMessage(uploadError, "save"));
        }
      }
    } catch (err: unknown) {
      setError(getPhotoActionErrorMessage(err, "save"));
    } finally {
      setUploading(false);
    }
  }

  async function removePhoto() {
    if (disabled) {
      return;
    }

    setError("");
    setUploading(true);

    try {
      if (isOnline && hasServerPhoto) {
        const response = await apiFetch(
          `/field-reports/visits/${reportId}/lines/${lineId}/photo`,
          { method: "DELETE" }
        );

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(
            payload.error?.message
              || payload.message
              || "מחיקת התמונה נכשלה"
          );
        }
      }

      await deleteLinePhotoLocally(reportId, lineId);

      if (previewUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(previewUrl);
      }
      setPreviewUrl(null);
      setPendingLocal(false);
      onPhotoChange?.(false);
    } catch (err: unknown) {
      setError(getPhotoActionErrorMessage(err, "delete"));
    } finally {
      setUploading(false);
    }
  }

  async function openCameraPicker() {
    if (disabled || uploading) {
      return;
    }

    setError("");
    const permissionState = await checkCameraPermission();

    if (permissionState === "denied") {
      setCameraBlocked(true);
      setError(
        "הגישה למצלמה חסומה בדפדפן. אפשר לאפשר הרשאה בהגדרות או להמשיך דרך בחירה מהגלריה."
      );
      return;
    }

    setCameraBlocked(false);
    cameraInputRef.current?.click();
  }

  return (
    <div className="mt-3 space-y-2">
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        disabled={disabled || uploading}
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null;
          void handleFileSelected(file);
          event.target.value = "";
        }}
      />
      <input
        ref={galleryInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        disabled={disabled || uploading}
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null;
          void handleFileSelected(file);
          event.target.value = "";
        }}
      />

      {previewUrl ? (
        <div className="space-y-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt="תמונת ממצא"
            className="max-h-56 w-full rounded-lg border border-zinc-200 object-cover lg:max-h-48"
          />
          {pendingLocal ? (
            <p className="text-xs text-amber-700">
              נשמר במכשיר — יועלה לשרת כשתחזור רשת
            </p>
          ) : null}
          {!disabled ? (
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                size="lg"
                className={`flex-1 sm:flex-none ${FR_TOUCH_BUTTON}`}
                type="button"
                disabled={uploading}
                onClick={() => void openCameraPicker()}
              >
                החלף תמונה
              </Button>
              <Button
                variant="secondary"
                size="lg"
                className={`flex-1 sm:flex-none ${FR_TOUCH_BUTTON}`}
                type="button"
                disabled={uploading}
                onClick={() => galleryInputRef.current?.click()}
              >
                בחר מהגלריה
              </Button>
              <Button
                variant="secondary"
                size="lg"
                className={`flex-1 sm:flex-none ${FR_TOUCH_BUTTON}`}
                type="button"
                disabled={uploading}
                onClick={() => void removePhoto()}
              >
                הסר תמונה
              </Button>
            </div>
          ) : null}
        </div>
      ) : !disabled ? (
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            size="lg"
            className={`flex-1 sm:flex-none ${FR_TOUCH_BUTTON}`}
            type="button"
            disabled={uploading}
            onClick={() => void openCameraPicker()}
          >
            {uploading ? "שומר תמונה..." : "צלם תמונה"}
          </Button>
          <Button
            variant="secondary"
            size="lg"
            className={`flex-1 sm:flex-none ${FR_TOUCH_BUTTON}`}
            type="button"
            disabled={uploading}
            onClick={() => galleryInputRef.current?.click()}
          >
            בחר מהגלריה
          </Button>
        </div>
      ) : null}

      {cameraBlocked ? (
        <p className="text-xs text-amber-700">
          ניתן להמשיך בדוח גם בלי תמונה, או לצרף תמונה קיימת מהגלריה.
        </p>
      ) : null}
      {error ? <p className="text-xs text-red-600">{error}</p> : null}
    </div>
  );
}

async function checkCameraPermission(): Promise<"granted" | "denied" | "unknown"> {
  if (typeof navigator === "undefined") {
    return "unknown";
  }

  const nav = navigator as Navigator & {
    permissions?: {
      query: (args: { name: "camera" }) => Promise<{ state: string }>;
    };
  };
  try {
    if (nav.permissions?.query) {
      const result = await nav.permissions.query({ name: "camera" });
      if (result.state === "denied") {
        return "denied";
      }
      if (result.state === "granted") {
        return "granted";
      }
    }
  } catch {
    // Some browsers do not support querying camera permission.
  }

  try {
    if (nav.mediaDevices?.getUserMedia) {
      const stream = await nav.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
      });
      stream.getTracks().forEach((track) => track.stop());
      return "granted";
    }
  } catch (err) {
    if (
      err instanceof DOMException
      && (err.name === "NotAllowedError" || err.name === "SecurityError")
    ) {
      return "denied";
    }
  }

  return "unknown";
}

function getPhotoActionErrorMessage(
  err: unknown,
  action: "save" | "delete"
): string {
  const fallback =
    action === "save"
      ? "לא הצלחנו לשמור את התמונה. אפשר להמשיך בדוח ולנסות שוב בעוד רגע."
      : "לא הצלחנו להסיר את התמונה כרגע. אפשר להמשיך בדוח ולנסות שוב.";

  if (!(err instanceof Error) || !err.message) {
    return fallback;
  }

  const message = err.message.toLowerCase();
  if (message.includes("network") || message.includes("failed to fetch")) {
    return "אין כרגע חיבור יציב לרשת. התמונה נשמרה מקומית ותסונכרן כשיהיה חיבור.";
  }
  if (
    message.includes("permission")
    || message.includes("denied")
    || message.includes("notallowederror")
  ) {
    return "אין הרשאת מצלמה בדפדפן. אפשר לאפשר הרשאה או לבחור תמונה מהגלריה.";
  }

  return err.message;
}
