"use client";

import { useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button";
import {
  pickLinePhotoFromNativeGallery,
  useNativeLinePhotoGallery,
} from "@/lib/capacitor/line-photo-picker";
import { apiFetch } from "@/lib/api/client";
import { MAX_LINE_PHOTOS } from "@/lib/field-reports/line-photo-constants";
import {
  canAddLinePhoto,
  countLinePhotosLocally,
  createLinePhotoObjectUrl,
  deleteLinePhotoLocally,
  listLinePhotosForLine,
  saveLinePhotoLocally,
} from "@/lib/field-reports/line-photo-store";
import { persistCapacitorRouteNow } from "@/components/capacitor/CapacitorRoutePersistence";
import { FR_TOUCH_BUTTON } from "@/lib/field-reports/touch-input-class";
import { useOffline } from "@/providers/OfflineProvider";

export type LinePhotoSummary = {
  id: string;
  url: string;
};

export type LinePhotosChangePayload = {
  has_photo: boolean;
  photo_ids: string[];
  photos: LinePhotoSummary[];
  photo_url: string | null;
};

type LinePhotoCaptureProps = {
  reportId: string;
  lineId: string;
  photos?: LinePhotoSummary[];
  hasServerPhoto?: boolean;
  photoUrl?: string | null;
  disabled?: boolean;
  onPhotosChange?: (payload: LinePhotosChangePayload) => void;
};

type PreviewItem = {
  id: string;
  url: string;
  pendingLocal: boolean;
};

export default function LinePhotoCapture({
  reportId,
  lineId,
  photos = [],
  hasServerPhoto = false,
  photoUrl,
  disabled = false,
  onPhotosChange,
}: LinePhotoCaptureProps) {
  const { isOnline } = useOffline();
  const nativeGalleryPicker = useNativeLinePhotoGallery();
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);
  const [previews, setPreviews] = useState<PreviewItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [cameraBlocked, setCameraBlocked] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const objectUrls: string[] = [];

    async function loadPreviews() {
      setError("");
      const remotePhotos =
        photos.length > 0
          ? photos
          : hasServerPhoto && photoUrl
            ? [{ id: "legacy", url: photoUrl }]
            : [];
      const items: PreviewItem[] = [];
      const localPhotos = await listLinePhotosForLine(reportId, lineId);

      for (const local of localPhotos) {
        const url = createLinePhotoObjectUrl(local.blob);
        objectUrls.push(url);
        items.push({
          id: local.photoId,
          url,
          pendingLocal: local.pendingUpload,
        });
      }

      for (const remote of remotePhotos) {
        if (items.some((item) => item.id === remote.id)) {
          continue;
        }

        if (!isOnline) {
          continue;
        }

        const response = await apiFetch(remote.url);
        if (!response.ok) {
          continue;
        }
        const blob = await response.blob();
        if (cancelled) {
          continue;
        }
        const url = createLinePhotoObjectUrl(blob);
        objectUrls.push(url);
        items.push({
          id: remote.id,
          url,
          pendingLocal: false,
        });
      }

      if (!cancelled) {
        setPreviews(items);
      }
    }

    void loadPreviews();

    return () => {
      cancelled = true;
      for (const url of objectUrls) {
        URL.revokeObjectURL(url);
      }
    };
  }, [hasServerPhoto, isOnline, lineId, photoUrl, photos, reportId]);

  useEffect(() => {
    return () => {
      for (const preview of previews) {
        if (preview.url.startsWith("blob:")) {
          URL.revokeObjectURL(preview.url);
        }
      }
    };
  }, [previews]);

  function emitFromLine(line: Record<string, unknown>) {
    const photoIds = Array.isArray(line.photo_ids)
      ? line.photo_ids.map(String)
      : [];
    const photoList = Array.isArray(line.photos)
      ? line.photos.map((photo) => ({
          id: String((photo as { id: string }).id),
          url: String((photo as { url: string }).url),
        }))
      : [];

    onPhotosChange?.({
      has_photo: Boolean(line.has_photo),
      photo_ids: photoIds,
      photos: photoList,
      photo_url:
        typeof line.photo_url === "string" ? line.photo_url : null,
    });
  }

  async function handleFileSelected(file: File | null) {
    if (!file || disabled) {
      return;
    }

    const remoteCount =
      photos.length > 0
        ? photos.length
        : hasServerPhoto
          ? 1
          : 0;
    const localCount = await countLinePhotosLocally(reportId, lineId);
    const totalCount = Math.max(localCount, remoteCount);
    if (!canAddLinePhoto(totalCount)) {
      setError(`ניתן לצרף עד ${MAX_LINE_PHOTOS} תמונות לשורה`);
      return;
    }

    setError("");
    setCameraBlocked(false);
    setUploading(true);

    try {
      const localPhotoId = await saveLinePhotoLocally(reportId, lineId, file, {
        pendingUpload: !isOnline,
      });

      if (isOnline) {
        try {
          const formData = new FormData();
          formData.append("file", file, file.name || "line-photo.jpg");

          const endpoint =
            remoteCount === 0
              ? `/field-reports/visits/${reportId}/lines/${lineId}/photo`
              : `/field-reports/visits/${reportId}/lines/${lineId}/photos`;

          const response = await apiFetch(endpoint, {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(
              payload.error?.message
                || payload.message
                || "העלאת התמונה נכשלה"
            );
          }

          const line = await response.json();
          await deleteLinePhotoLocally(reportId, lineId, localPhotoId);
          emitFromLine(line);
        } catch (uploadError: unknown) {
          await saveLinePhotoLocally(reportId, lineId, file, {
            pendingUpload: true,
            photoId: localPhotoId,
          });
          setError(getPhotoActionErrorMessage(uploadError, "save"));
        }
      } else {
        onPhotosChange?.({
          has_photo: true,
          photo_ids: [...photos.map((photo) => photo.id), localPhotoId],
          photos,
          photo_url: photoUrl ?? null,
        });
      }
    } catch (err: unknown) {
      setError(getPhotoActionErrorMessage(err, "save"));
    } finally {
      setUploading(false);
    }
  }

  async function removePhoto(photoId: string) {
    if (disabled) {
      return;
    }

    setError("");
    setUploading(true);

    try {
      if (isOnline) {
        const endpoint =
          photoId === "legacy"
            ? `/field-reports/visits/${reportId}/lines/${lineId}/photo`
            : `/field-reports/visits/${reportId}/lines/${lineId}/photos/${photoId}`;

        const response = await apiFetch(endpoint, { method: "DELETE" });

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(
            payload.error?.message
              || payload.message
              || "מחיקת התמונה נכשלה"
          );
        }

        const line = await response.json();
        emitFromLine(line);
      }

      await deleteLinePhotoLocally(reportId, lineId, photoId);
      setPreviews((current) => current.filter((item) => item.id !== photoId));

      if (!isOnline) {
        const remaining = photos.filter((photo) => photo.id !== photoId);
        onPhotosChange?.({
          has_photo: remaining.length > 0,
          photo_ids: remaining.map((photo) => photo.id),
          photos: remaining,
          photo_url: remaining[0]?.url ?? null,
        });
      }
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
    setCameraBlocked(false);

    const permissionState = await checkCameraPermission();

    if (permissionState === "denied") {
      setCameraBlocked(true);
      setError(
        "הגישה למצלמה חסומה בדפדפן. אפשר לאפשר הרשאה בהגדרות או להמשיך דרך בחירה מהגלריה."
      );
      return;
    }

    cameraInputRef.current?.click();
  }

  async function openGalleryPicker() {
    if (disabled || uploading) {
      return;
    }

    setError("");

    if (nativeGalleryPicker) {
      persistCapacitorRouteNow();
      try {
        const file = await pickLinePhotoFromNativeGallery();
        if (file) {
          await handleFileSelected(file);
        }
      } catch (err: unknown) {
        setError(getPhotoActionErrorMessage(err, "save"));
      }

      return;
    }

    galleryInputRef.current?.click();
  }

  const canAddMore = canAddLinePhoto(
    Math.max(
      previews.length,
      photos.length > 0 ? photos.length : hasServerPhoto ? 1 : 0
    )
  );

  return (
    <div className="mt-3 space-y-2 rounded-lg border border-dashed border-zinc-300 bg-white/80 p-3 dark:border-zinc-700 dark:bg-zinc-900/40">
      <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
        תמונות לשורה
      </p>
      <p className="text-xs text-zinc-500">
        עד {MAX_LINE_PHOTOS} תמונות — נשמרות במכשיר ומסתנכרנות לשרת כשיש רשת.
      </p>
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        disabled={disabled || uploading || !canAddMore}
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
        disabled={disabled || uploading || !canAddMore}
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null;
          void handleFileSelected(file);
          event.target.value = "";
        }}
      />

      {previews.length > 0 ? (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            {previews.map((preview) => (
              <div
                key={preview.id}
                className="relative w-24 shrink-0 space-y-1"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={preview.url}
                  alt="תמונת ממצא"
                  className="h-24 w-24 rounded-lg border border-zinc-200 object-cover"
                />
                {preview.pendingLocal ? (
                  <p className="text-[10px] text-amber-700">ממתין לרשת</p>
                ) : null}
                {!disabled ? (
                  <button
                    type="button"
                    className="w-full rounded border border-zinc-200 px-1 py-1 text-[11px] text-zinc-600"
                    disabled={uploading}
                    onClick={() => void removePhoto(preview.id)}
                  >
                    הסר
                  </button>
                ) : null}
              </div>
            ))}
          </div>
          {!disabled && canAddMore ? (
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                size="lg"
                className={`flex-1 sm:flex-none ${FR_TOUCH_BUTTON}`}
                type="button"
                disabled={uploading}
                onClick={() => void openCameraPicker()}
              >
                {uploading ? "שומר..." : "צלם תמונה"}
              </Button>
              <Button
                variant="secondary"
                size="lg"
                className={`flex-1 sm:flex-none ${FR_TOUCH_BUTTON}`}
                type="button"
                disabled={uploading}
                onClick={() => void openGalleryPicker()}
              >
                הוסף מהגלריה
              </Button>
            </div>
          ) : null}
          {!canAddMore ? (
            <p className="text-xs text-zinc-500">
              {`הגעת למקסימום ${MAX_LINE_PHOTOS} תמונות לשורה`}
            </p>
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
            onClick={() => void openGalleryPicker()}
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
