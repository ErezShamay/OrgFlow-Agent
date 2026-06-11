import type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";

import { ELAYOAI_FIELD_REPORTS_OFFLINE_PREFIX } from "@/lib/elayoai/keys";

const STORAGE_PREFIX = ELAYOAI_FIELD_REPORTS_OFFLINE_PREFIX;

function storageKey(organizationId: string) {
  return `${STORAGE_PREFIX}:${organizationId}`;
}

/** קריאת legacy מ-localStorage (לפני מיגרציה ל-IndexedDB). */
export function readLegacyOfflinePrepBundle(
  organizationId: string
): OfflinePrepBundle | null {
  if (!organizationId || typeof localStorage === "undefined") {
    return null;
  }

  const raw = localStorage.getItem(storageKey(organizationId));
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as OfflinePrepBundle;
  } catch {
    return null;
  }
}

export function clearLegacyOfflinePrepBundle(organizationId: string) {
  if (!organizationId || typeof localStorage === "undefined") {
    return;
  }

  localStorage.removeItem(storageKey(organizationId));
}

/** שמירת legacy - לבדיקות מיגרציה בלבד. */
export function writeLegacyOfflinePrepBundle(
  organizationId: string,
  bundle: OfflinePrepBundle
) {
  if (!organizationId || typeof localStorage === "undefined") {
    return;
  }

  localStorage.setItem(storageKey(organizationId), JSON.stringify(bundle));
}
