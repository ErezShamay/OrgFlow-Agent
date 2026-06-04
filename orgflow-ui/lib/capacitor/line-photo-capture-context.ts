import { canUseCapacitorWebStorage } from "@/lib/capacitor/platform";

export const LINE_PHOTO_CAPTURE_CONTEXT_KEY =
  "elayoai-line-photo-capture-context";
const MAX_AGE_MS = 10 * 60 * 1000;

export type LinePhotoCaptureContext = {
  returnPath: string;
  reportId: string;
  lineId: string;
  startedAt: number;
};

function canPersist(): boolean {
  return (
    canUseCapacitorWebStorage()
    && typeof window.localStorage !== "undefined"
  );
}

export function writeLinePhotoCaptureContext(
  context: Omit<LinePhotoCaptureContext, "startedAt">
): void {
  if (!canPersist()) {
    return;
  }

  const payload: LinePhotoCaptureContext = {
    ...context,
    startedAt: Date.now(),
  };

  window.localStorage.setItem(
    LINE_PHOTO_CAPTURE_CONTEXT_KEY,
    JSON.stringify(payload)
  );
  return;
}

export function readLinePhotoCaptureContext(): LinePhotoCaptureContext | null {
  if (!canPersist()) {
    return null;
  }

  const raw = window.localStorage.getItem(LINE_PHOTO_CAPTURE_CONTEXT_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as LinePhotoCaptureContext;
    if (
      !parsed.returnPath?.trim()
      || !parsed.reportId?.trim()
      || !parsed.lineId?.trim()
      || typeof parsed.startedAt !== "number"
    ) {
      return null;
    }

    if (Date.now() - parsed.startedAt > MAX_AGE_MS) {
      clearLinePhotoCaptureContext();
      return null;
    }

    return parsed;
  } catch {
    clearLinePhotoCaptureContext();
    return null;
  }
}

export function clearLinePhotoCaptureContext(): void {
  if (!canPersist()) {
    return;
  }

  window.localStorage.removeItem(LINE_PHOTO_CAPTURE_CONTEXT_KEY);
}

export function linePhotoCaptureResumeMessage(
  context: LinePhotoCaptureContext,
  reportId: string,
  lineId: string
): string | null {
  if (context.reportId !== reportId || context.lineId !== lineId) {
    return null;
  }

  return "האפליקציה נטענה מחדש אחרי המצלמה. צלם שוב או בחר תמונה מהגלריה.";
}
