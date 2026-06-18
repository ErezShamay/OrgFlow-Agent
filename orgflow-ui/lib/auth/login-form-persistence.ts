import { ELAYOAI_LOGIN_SAVED_EMAIL_KEY } from "@/lib/elayoai/keys";

export function readSavedLoginEmail(): string {
  if (typeof localStorage === "undefined") {
    return "";
  }

  return localStorage.getItem(ELAYOAI_LOGIN_SAVED_EMAIL_KEY)?.trim() || "";
}

export function saveLoginEmail(email: string): void {
  if (typeof localStorage === "undefined") {
    return;
  }

  const trimmed = email.trim();
  if (!trimmed) {
    clearSavedLoginEmail();
    return;
  }

  localStorage.setItem(ELAYOAI_LOGIN_SAVED_EMAIL_KEY, trimmed);
}

export function clearSavedLoginEmail(): void {
  if (typeof localStorage === "undefined") {
    return;
  }

  localStorage.removeItem(ELAYOAI_LOGIN_SAVED_EMAIL_KEY);
}
