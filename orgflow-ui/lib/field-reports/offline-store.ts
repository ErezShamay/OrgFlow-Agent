import type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";
import { clearLegacyOfflinePrepBundle } from "@/lib/field-reports/offline-prep-local-storage";
import {
  clearCatalogBundle,
  resolveOfflinePrepBundle,
  saveFromOfflinePrep,
} from "@/lib/field-reports/repositories/catalog-repository";
import { clearOpenIssuesOfflineCache } from "@/lib/quality-issues/open-issues-offline";

export type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";

const prepBundleCache = new Map<string, OfflinePrepBundle>();

function setCachedOfflinePrepBundle(
  organizationId: string,
  bundle: OfflinePrepBundle | null
) {
  if (!bundle) {
    prepBundleCache.delete(organizationId);
    return;
  }

  prepBundleCache.set(organizationId, bundle);
}

/**
 * טוען חבילת הכנה ל-IndexedDB ומעדכן מטמון סינכרוני לקריאות UI.
 */
export async function hydrateOfflinePrepBundle(
  organizationId: string
): Promise<OfflinePrepBundle | null> {
  if (!organizationId) {
    setCachedOfflinePrepBundle(organizationId, null);
    return null;
  }

  const bundle = await resolveOfflinePrepBundle(organizationId);
  setCachedOfflinePrepBundle(organizationId, bundle);
  return bundle;
}

/** קריאה סינכרונית מהמטמון - אחרי `hydrateOfflinePrepBundle`. */
export function loadOfflinePrepBundle(
  organizationId: string
): OfflinePrepBundle | null {
  if (!organizationId) {
    return null;
  }

  return prepBundleCache.get(organizationId) ?? null;
}

export async function saveOfflinePrepBundle(
  organizationId: string,
  bundle: Omit<OfflinePrepBundle, "prepared_at" | "expires_at">
): Promise<OfflinePrepBundle> {
  const saved = await saveFromOfflinePrep(organizationId, bundle);
  clearLegacyOfflinePrepBundle(organizationId);
  setCachedOfflinePrepBundle(organizationId, saved);
  return saved;
}

export function isOfflinePrepValid(
  bundle: OfflinePrepBundle | null
): boolean {
  if (!bundle?.expires_at) {
    return false;
  }

  return new Date(bundle.expires_at).getTime() > Date.now();
}

export async function clearOfflinePrepBundle(organizationId: string) {
  if (!organizationId || typeof localStorage === "undefined") {
    return;
  }

  clearLegacyOfflinePrepBundle(organizationId);
  setCachedOfflinePrepBundle(organizationId, null);
  await clearCatalogBundle(organizationId);
  await clearOpenIssuesOfflineCache(organizationId);
}
