"use client";

import { useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import { showToast } from "@/lib/ui/toast";

const DEFAULT_ILLUSTRATION_SOURCE_HE =
  'התמונה נלקחה מאתר מדלן';

type ProjectIllustrationUploadProps = {
  projectId: string;
  illustrationUrl?: string | null;
  illustrationSourceHe?: string | null;
  canEdit: boolean;
  onUploaded: () => void | Promise<void>;
};

export default function ProjectIllustrationUpload({
  projectId,
  illustrationUrl,
  illustrationSourceHe,
  canEdit,
  onUploaded,
}: ProjectIllustrationUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sourceHe, setSourceHe] = useState(
    illustrationSourceHe?.trim() || ""
  );
  const [savingSource, setSavingSource] = useState(false);

  useEffect(() => {
    if (!illustrationUrl) {
      setPreviewUrl(null);
      return;
    }

    let active = true;
    let objectUrl: string | null = null;

    async function loadPreview() {
      try {
        setLoadingPreview(true);
        const response = await apiFetch(
          `/projects/${projectId}/illustration`
        );
        if (!response.ok) {
          return;
        }
        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        if (active) {
          setPreviewUrl(objectUrl);
        }
      } finally {
        if (active) {
          setLoadingPreview(false);
        }
      }
    }

    void loadPreview();

    return () => {
      active = false;
      if (objectUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [projectId, illustrationUrl]);

  useEffect(() => {
    return () => {
      if (previewUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  useEffect(() => {
    setSourceHe(illustrationSourceHe?.trim() || "");
  }, [illustrationSourceHe]);

  async function handleSaveSource() {
    if (!canEdit) {
      return;
    }

    try {
      setSavingSource(true);
      const response = await apiFetch(`/projects/${projectId}`, {
        method: "PATCH",
        body: JSON.stringify({
          illustration_source_he: sourceHe.trim() || null,
        }),
      });

      if (!response.ok) {
        throw new Error("שמירת מקור התמונה נכשלה");
      }

      showToast("מקור התמונה נשמר", "success");
      await onUploaded();
    } catch (error: unknown) {
      showToast(
        error instanceof Error ? error.message : "שמירת מקור התמונה נכשלה",
        "error"
      );
    } finally {
      setSavingSource(false);
    }
  }

  async function handleFileSelected(file: File | null) {
    if (!file || !canEdit) {
      return;
    }

    if (!file.type.startsWith("image/")) {
      showToast("יש להעלות קובץ תמונה בלבד", "error");
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.set("file", file, file.name);

      const response = await apiFetch(
        `/projects/${projectId}/illustration`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(
          (payload as { error?: { message?: string }; message?: string })
            .error?.message
            || (payload as { message?: string }).message
            || "העלאת תמונת ההדמיה נכשלה"
        );
      }

      showToast("תמונת ההדמיה נשמרה בפרויקט", "success");
      await onUploaded();
    } catch (error: unknown) {
      showToast(
        error instanceof Error
          ? error.message
          : "העלאת תמונת ההדמיה נכשלה",
        "error"
      );
    } finally {
      setUploading(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <section className="space-y-4 rounded-2xl border border-zinc-200/80 bg-zinc-50/50 p-6 dark:border-zinc-700/80 dark:bg-zinc-900/30">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">הדמיית הפרויקט</h3>
          <p className="mt-1 text-sm text-zinc-500">
            תמונה אחת לפרויקט - מופיעה בדוח השטח בעמוד ההדמיה (כמו בדוחות הלקוח).
          </p>
        </div>
        {canEdit ? (
          <>
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(event) =>
                void handleFileSelected(event.target.files?.[0] ?? null)
              }
            />
            <Button
              type="button"
              variant="secondary"
              disabled={uploading}
              onClick={() => inputRef.current?.click()}
            >
              {uploading
                ? "מעלה..."
                : illustrationUrl
                  ? "החלף תמונה"
                  : "העלה תמונה"}
            </Button>
          </>
        ) : null}
      </div>

      {loadingPreview ? (
        <p className="text-sm text-zinc-500">טוען תצוגה מקדימה...</p>
      ) : null}

      {!loadingPreview && previewUrl ? (
        <img
          src={previewUrl}
          alt="הדמיית הפרויקט"
          className="max-h-80 w-full rounded-xl border border-zinc-200 object-contain bg-white dark:border-zinc-700 dark:bg-zinc-900"
        />
      ) : null}

      {!loadingPreview && !previewUrl ? (
        <p className="text-sm text-zinc-500">
          {illustrationUrl
            ? "לא ניתן להציג את התמונה כרגע"
            : "טרם הועלתה תמונת הדמיה לפרויקט"}
        </p>
      ) : null}

      <div className="space-y-3 border-t border-zinc-200 pt-4 dark:border-zinc-700">
        <label className="block space-y-2">
          <span className="text-sm font-medium text-zinc-600 dark:text-zinc-300">
            כיתוב מקור התמונה (מופיע בדוח PDF)
          </span>
          <input
            className="w-full rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-base dark:border-zinc-700 dark:bg-zinc-900/50"
            value={sourceHe}
            onChange={(event) => setSourceHe(event.target.value)}
            placeholder={DEFAULT_ILLUSTRATION_SOURCE_HE}
            disabled={!canEdit || savingSource}
          />
        </label>
        {canEdit ? (
          <Button
            type="button"
            variant="secondary"
            disabled={savingSource}
            onClick={() => void handleSaveSource()}
          >
            {savingSource ? "שומר..." : "שמירת מקור התמונה"}
          </Button>
        ) : sourceHe ? (
          <p className="text-sm text-zinc-600 dark:text-zinc-300">{sourceHe}</p>
        ) : null}
      </div>
    </section>
  );
}
