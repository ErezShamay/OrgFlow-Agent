"use client";

import { useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button";
import { buildIssuePhotoPath } from "@/lib/quality-issues/api";
import { uploadRemediationPhoto } from "@/lib/quality-issues/remediation-photo-upload";

export type RemediationPhotoPreview = {
  photoId: string;
  previewUrl: string;
};

type RemediationPhotoUploadProps = {
  issueId: string;
  disabled?: boolean;
  onPhotosChange?: (photoIds: string[]) => void;
  className?: string;
};

export default function RemediationPhotoUpload({
  issueId,
  disabled = false,
  onPhotosChange,
  className = "",
}: RemediationPhotoUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [previews, setPreviews] = useState<RemediationPhotoPreview[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    return () => {
      for (const preview of previews) {
        if (preview.previewUrl.startsWith("blob:")) {
          URL.revokeObjectURL(preview.previewUrl);
        }
      }
    };
  }, [previews]);

  useEffect(() => {
    onPhotosChange?.(previews.map((preview) => preview.photoId));
  }, [onPhotosChange, previews]);

  async function handleFileSelected(file: File | null | undefined) {
    if (!file || disabled || uploading) {
      return;
    }

    const localPreview = URL.createObjectURL(file);
    setUploading(true);
    setError("");

    try {
      const uploaded = await uploadRemediationPhoto(issueId, file);
      setPreviews((current) => [
        ...current,
        {
          photoId: uploaded.photoId,
          previewUrl: buildIssuePhotoPath(issueId, uploaded.photoId),
        },
      ]);
      URL.revokeObjectURL(localPreview);
    } catch (uploadError) {
      URL.revokeObjectURL(localPreview);
      const message =
        uploadError instanceof Error
          ? uploadError.message
          : "העלאת תמונת התיקון נכשלה";
      setError(message);
    } finally {
      setUploading(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <label className="block space-y-1.5 text-sm">
        <span className="font-medium text-zinc-700 dark:text-zinc-300">
          תמונת תיקון (חובה)
        </span>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          disabled={disabled || uploading}
          onChange={(event) => {
            void handleFileSelected(event.target.files?.[0]);
          }}
        />
        <Button
          type="button"
          variant="secondary"
          disabled={disabled || uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? "מעלה תמונה..." : "העלה תמונת תיקון"}
        </Button>
      </label>

      {previews.length > 0 ? (
        <ul className="flex flex-wrap gap-3">
          {previews.map((preview) => (
            <li key={preview.photoId}>
              <img
                src={preview.previewUrl}
                alt="תמונת תיקון"
                className="h-24 w-24 rounded-lg border border-zinc-200 object-cover dark:border-zinc-700"
              />
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-xs text-zinc-500">
          העלו לפחות תמונה אחת כהוכחת ביצוע התיקון לפני שליחה למפקח.
        </p>
      )}

      {error ? (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      ) : null}
    </div>
  );
}
