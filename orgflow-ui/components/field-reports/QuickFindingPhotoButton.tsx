"use client";

import { useMemo, useRef, useState } from "react";
import { Camera } from "lucide-react";

import Button from "@/components/ui/Button";
import { persistCapacitorRouteNow } from "@/components/capacitor/CapacitorRoutePersistence";
import { isLikelyAndroidEmulator } from "@/lib/capacitor/android-emulator";
import { writeLinePhotoCaptureContext } from "@/lib/capacitor/line-photo-capture-context";
import { currentDocumentPath } from "@/lib/capacitor/route-persistence";
import { QUICK_FINDING_PHOTO_TAP_COUNT } from "@/lib/field-reports/quick-finding-photo";
import { FR_TOUCH_BUTTON } from "@/lib/field-reports/touch-input-class";

type QuickFindingPhotoButtonProps = {
  reportId: string;
  disabled?: boolean;
  busy?: boolean;
  onPhotoCaptured: (file: File) => void | Promise<void>;
};

export default function QuickFindingPhotoButton({
  reportId,
  disabled = false,
  busy = false,
  onPhotoCaptured,
}: QuickFindingPhotoButtonProps) {
  const androidEmulator = useMemo(() => isLikelyAndroidEmulator(), []);
  const useDeviceCameraCapture = !androidEmulator;
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const isDisabled = disabled || busy || processing;

  function persistRouteBeforeCapture() {
    persistCapacitorRouteNow();
    writeLinePhotoCaptureContext({
      returnPath: currentDocumentPath(),
      reportId,
      lineId: "quick-finding-pending",
    });
  }

  function openCamera() {
    if (isDisabled) {
      return;
    }

    setError("");
    persistRouteBeforeCapture();
    cameraInputRef.current?.click();
  }

  async function handleFileSelected(file: File | null) {
    if (!file || isDisabled) {
      return;
    }

    setProcessing(true);
    setError("");

    try {
      await onPhotoCaptured(file);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "יצירת שורת ממצא מתמונה נכשלה"
      );
    } finally {
      setProcessing(false);
    }
  }

  return (
    <div className="space-y-2 rounded-xl border border-brand/30 bg-brand/5 p-4 dark:border-brand/40 dark:bg-brand/10">
      <div className="space-y-1">
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          צילום מהיר - ממצא חדש
        </p>
        <p className="text-xs text-zinc-600 dark:text-zinc-400">
          {QUICK_FINDING_PHOTO_TAP_COUNT} לחיצות: «צלם ממצא» → צילום. נוצרת
          שורה עם תמונה; אפשר לערוך תיאור אחר כך.
        </p>
        {androidEmulator ? (
          <p className="text-xs text-amber-800 dark:text-amber-300">
            באמולטור הכפתור פותח בחירת קובץ במקום מצלמה.
          </p>
        ) : null}
      </div>

      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        {...(useDeviceCameraCapture
          ? { capture: "environment" as const }
          : {})}
        className="hidden"
        disabled={isDisabled}
        onChange={(event) => {
          const file = event.target.files?.[0] ?? null;
          void handleFileSelected(file);
          event.target.value = "";
        }}
      />

      <Button
        type="button"
        size="lg"
        className={`w-full sm:w-auto ${FR_TOUCH_BUTTON}`}
        disabled={isDisabled}
        onClick={openCamera}
      >
        <Camera className="h-5 w-5 shrink-0" aria-hidden />
        {processing || busy ? "שומר ממצא..." : "צלם ממצא"}
      </Button>

      {error ? (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
