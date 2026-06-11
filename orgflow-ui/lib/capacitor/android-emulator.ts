/** זיהוי אמולטור Android - במצלמה וירטואלית עדיף גלריה/קובץ בלי `capture`. */
export function isLikelyAndroidEmulator(): boolean {
  if (typeof navigator === "undefined") {
    return false;
  }

  const ua = navigator.userAgent;
  return /sdk_gphone|sdk_google_phone|Android SDK built for|emulator/i.test(
    ua
  );
}
