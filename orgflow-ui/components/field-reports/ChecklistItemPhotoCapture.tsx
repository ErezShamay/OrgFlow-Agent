"use client";

import { useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button";
import {
  pickLinePhotoFromNativeGallery,
  isNativeLinePhotoGallery,
} from "@/lib/capacitor/line-photo-picker";
import { isLikelyAndroidEmulator } from "@/lib/capacitor/android-emulator";
import {
  canAddChecklistPhoto,
  countChecklistPhotosLocally,
  createChecklistPhotoObjectUrl,
  deleteChecklistPhotoLocally,
  listChecklistPhotosForItem,
  MAX_CHECKLIST_ITEM_PHOTOS,
  saveChecklistPhotoLocally,
} from "@/lib/field-reports/checklist-photo-store";
import { nextChecklistPhotoSlotId } from "@/lib/field-reports/checklist-photo-keys";
import { FR_TOUCH_BUTTON } from "@/lib/field-reports/touch-input-class";

type ChecklistItemPhotoCaptureProps = {
  reportId: string;
  checklistItemId: string;
  photoIds: string[];
  disabled?: boolean;
  onPhotoIdsChange: (photoIds: string[]) => void;
};

type PreviewItem = {
  id: string;
  url: string;
  pendingLocal: boolean;
};

export default function ChecklistItemPhotoCapture({
  reportId,
  checklistItemId,
  photoIds,
  disabled = false,
  onPhotoIdsChange,
}: ChecklistItemPhotoCaptureProps) {
  const nativeGalleryPicker = isNativeLinePhotoGallery();
  const androidEmulator = isLikelyAndroidEmulator();
  const useDeviceCameraCapture = !androidEmulator;
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);
  const [previews, setPreviews] = useState<PreviewItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const objectUrls: string[] = [];

    async function loadPreviews() {
      setError("");
      const items: PreviewItem[] = [];
      const localPhotos = await listChecklistPhotosForItem(
        reportId,
        checklistItemId
      );

      for (const local of localPhotos) {
        const url = createChecklistPhotoObjectUrl(local.blob);
        objectUrls.push(url);
        items.push({
          id: local.photoId,
          url,
          pendingLocal: local.pendingUpload,
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
  }, [checklistItemId, photoIds, reportId]);

  async function handleFileSelected(file: File | null) {
    if (!file || disabled) {
      return;
    }

    const localCount = await countChecklistPhotosLocally(
      reportId,
      checklistItemId
    );
    const totalCount = Math.max(localCount, photoIds.length);
    if (!canAddChecklistPhoto(totalCount)) {
      setError(`ניתן לצרף עד ${MAX_CHECKLIST_ITEM_PHOTOS} תמונות לפריט`);
      return;
    }

    const slotId = nextChecklistPhotoSlotId(photoIds);
    if (!slotId) {
      setError(`ניתן לצרף עד ${MAX_CHECKLIST_ITEM_PHOTOS} תמונות לפריט`);
      return;
    }

    setError("");
    setUploading(true);

    try {
      await saveChecklistPhotoLocally(reportId, checklistItemId, file, {
        pendingUpload: true,
        photoId: slotId,
      });

      const nextPhotoIds = [...photoIds, slotId].slice(
        0,
        MAX_CHECKLIST_ITEM_PHOTOS
      );
      onPhotoIdsChange(nextPhotoIds);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "לא הצלחנו לשמור את התמונה"
      );
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
      await deleteChecklistPhotoLocally(reportId, checklistItemId, photoId);
      onPhotoIdsChange(photoIds.filter((id) => id !== photoId));
      setPreviews((current) => current.filter((item) => item.id !== photoId));
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "לא הצלחנו להסיר את התמונה"
      );
    } finally {
      setUploading(false);
    }
  }

  const canAddMore = canAddChecklistPhoto(
    Math.max(previews.length, photoIds.length)
  );

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {previews.map((preview) => (
          <div key={preview.id} className="relative w-20 shrink-0 space-y-1">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={preview.url}
              alt="תמונת פריט"
              className="h-20 w-20 rounded-lg border border-zinc-200 object-cover"
            />
            {preview.pendingLocal ? (
              <p className="text-[10px] text-amber-700">נשמר מקומית</p>
            ) : null}
            {!disabled ? (
              <button
                type="button"
                className="w-full rounded border border-zinc-200 px-1 py-0.5 text-[10px] text-zinc-600"
                disabled={uploading}
                onClick={() => void removePhoto(preview.id)}
              >
                הסר
              </button>
            ) : null}
          </div>
        ))}

        {!disabled && canAddMore ? (
          <>
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              {...(useDeviceCameraCapture
                ? { capture: "environment" as const }
                : {})}
              className="hidden"
              disabled={uploading}
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
              disabled={uploading}
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                void handleFileSelected(file);
                event.target.value = "";
              }}
            />
            <Button
              variant="secondary"
              size="sm"
              type="button"
              className={FR_TOUCH_BUTTON}
              disabled={uploading}
              onClick={() => {
                if (androidEmulator) {
                  galleryInputRef.current?.click();
                  return;
                }
                cameraInputRef.current?.click();
              }}
            >
              📷
            </Button>
            <Button
              variant="secondary"
              size="sm"
              type="button"
              className={FR_TOUCH_BUTTON}
              disabled={uploading}
              onClick={() => {
                if (nativeGalleryPicker) {
                  void pickLinePhotoFromNativeGallery()
                    .then((file) => handleFileSelected(file))
                    .catch((err: unknown) => {
                      setError(
                        err instanceof Error
                          ? err.message
                          : "לא הצלחנו לשמור את התמונה"
                      );
                    });
                  return;
                }

                galleryInputRef.current?.click();
              }}
            >
              גלריה
            </Button>
          </>
        ) : null}
      </div>

      {!canAddMore ? (
        <p className="text-xs text-zinc-500">
          {`הגעת למקסימום ${MAX_CHECKLIST_ITEM_PHOTOS} תמונות לפריט`}
        </p>
      ) : null}

      {error ? <p className="text-xs text-red-600">{error}</p> : null}
    </div>
  );
}
