import {
  Camera,
  CameraDirection,
  type MediaResult,
} from "@capacitor/camera";

import {
  getCapacitorCameraErrorCode,
  isCapacitorCameraUserCancelled,
} from "@/lib/capacitor/camera-errors";
import { linePhotoMediaResultToFile } from "@/lib/capacitor/media-result-to-file";
import { isCapacitorNativePlatform } from "@/lib/capacitor/platform";

const LINE_PHOTO_QUALITY = 90;

/**
 * צילום ב-APK: תמיד `<input capture>` בתוך ה-WebView.
 * מצלמת Capacitor (`Camera.takePhoto`) פותחת אפליקציה חיצונית, טוענת מחדש את
 * ה-WebView ומעבירה לדף הבית — לא משתמשים בה ב-UI.
 */
export function useNativeLinePhotoCamera(): boolean {
  return false;
}

/** גלריה ב-APK — Photo Picker של Capacitor (ללא מצלמה מערכת). */
export function useNativeLinePhotoGallery(): boolean {
  return isCapacitorNativePlatform();
}

/** @deprecated השתמשו ב-`useNativeLinePhotoGallery`. */
export function useNativeLinePhotoPicker(): boolean {
  return useNativeLinePhotoGallery();
}

/**
 * צילום תמונת שורה במצלמת המכשיר (Capacitor native).
 * ב-UI לא נקרא — נשאר לבדיקות / שימוש ישיר.
 */
export async function takeLinePhotoWithNativeCamera(): Promise<File | null> {
  if (!isCapacitorNativePlatform()) {
    return null;
  }

  try {
    const result = await Camera.takePhoto({
      quality: LINE_PHOTO_QUALITY,
      cameraDirection: CameraDirection.Rear,
      includeMetadata: true,
    });

    return mediaResultToLinePhotoFile(result);
  } catch (err: unknown) {
    if (isCapacitorCameraUserCancelled(err)) {
      return null;
    }

    throw enrichNativeCameraError(err, "camera");
  }
}

/**
 * בחירת תמונת שורה מהגלריה (Capacitor native / Photo Picker).
 * מחזיר null אם המשתמש ביטל או לא נבחר קובץ.
 */
export async function pickLinePhotoFromNativeGallery(): Promise<File | null> {
  if (!useNativeLinePhotoGallery()) {
    return null;
  }

  try {
    const { results } = await Camera.chooseFromGallery({
      quality: LINE_PHOTO_QUALITY,
      allowMultipleSelection: false,
      limit: 1,
      includeMetadata: true,
    });

    const first = results[0];
    if (!first) {
      return null;
    }

    return mediaResultToLinePhotoFile(first);
  } catch (err: unknown) {
    if (isCapacitorCameraUserCancelled(err)) {
      return null;
    }

    throw enrichNativeCameraError(err, "gallery");
  }
}

async function mediaResultToLinePhotoFile(result: MediaResult): Promise<File> {
  return linePhotoMediaResultToFile(
    {
      webPath: result.webPath,
      metadata: result.metadata
        ? { format: result.metadata.format }
        : undefined,
    },
    { defaultBaseName: `line-photo-${Date.now()}` }
  );
}

function enrichNativeCameraError(
  err: unknown,
  source: "camera" | "gallery"
): Error {
  if (!(err instanceof Error)) {
    return new Error(
      source === "camera"
        ? "צילום התמונה נכשל"
        : "בחירת התמונה מהגלריה נכשלה"
    );
  }

  const code = getCapacitorCameraErrorCode(err);
  if (code === "OS-PLUG-CAMR-0003") {
    return new Error(
      "אין הרשאת מצלמה. אפשר לאפשר בהגדרות המכשיר או לבחור תמונה מהגלריה."
    );
  }

  if (code === "OS-PLUG-CAMR-0005") {
    return new Error(
      "אין גישה לגלריה. אפשר לאפשר בהגדרות המכשיר או לצלם תמונה חדשה."
    );
  }

  if (code === "OS-PLUG-CAMR-0007") {
    return new Error("לא נמצאה מצלמה במכשיר.");
  }

  return err;
}
