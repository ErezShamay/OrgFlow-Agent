"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";
import {
  fetchAndPersistOfflinePrepBundle,
  type OfflinePrepFetchResult,
} from "@/lib/field-reports/offline-prep-runner";
import { clearOfflinePrepUiDismiss } from "@/lib/field-reports/offline-prep-ui-dismiss";
import {
  clearOfflinePrepBundle,
  hydrateOfflinePrepBundle,
  isOfflinePrepValid,
  saveOfflinePrepBundle,
  type OfflinePrepBundle,
} from "@/lib/field-reports/offline-store";
import {
  hydrateOpenIssuesCache,
} from "@/lib/quality-issues/open-issues-offline";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { useOffline } from "@/providers/OfflineProvider";

type UseFieldReportOfflinePrepOptions = {
  autoPrepare?: boolean;
  projectId?: string;
};

export function useFieldReportOfflinePrep(
  options: UseFieldReportOfflinePrepOptions = {}
) {
  const { autoPrepare = true, projectId } = options;
  const { status } = useFieldReportModule();
  const { profile } = useAuth();
  const { isOnline } = useOffline();
  const organizationId = status?.organization_id || "";
  const isModuleEnabled = Boolean(status?.is_enabled);
  const [storedBundle, setStoredBundle] = useState<OfflinePrepBundle | null>(
    null
  );
  const [hydrating, setHydrating] = useState(false);
  const [preparedBundle, setPreparedBundle] = useState<{
    organizationId: string;
    bundle: OfflinePrepBundle;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState("");
  const [importSummary, setImportSummary] =
    useState<OfflinePrepFetchResult["importSummary"] | null>(null);
  const autoPrepareAttemptedRef = useRef(false);

  useEffect(() => {
    if (!organizationId || !isModuleEnabled) {
      setStoredBundle(null);
      return;
    }

    let cancelled = false;
    setHydrating(true);

    void hydrateOfflinePrepBundle(organizationId)
      .then((bundle) => {
        if (!cancelled) {
          setStoredBundle(bundle);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setHydrating(false);
        }
      });

    void hydrateOpenIssuesCache(organizationId);

    return () => {
      cancelled = true;
    };
  }, [organizationId, isModuleEnabled]);

  const bundle =
    isModuleEnabled
    && preparedBundle?.organizationId === organizationId
      ? preparedBundle.bundle
      : storedBundle;

  const applyPrepResult = useCallback(
    (result: OfflinePrepFetchResult) => {
      setImportSummary(result.importSummary);
      setPreparedBundle({
        organizationId,
        bundle: result.bundle,
      });
      setStoredBundle(result.bundle);
      return result.bundle;
    },
    [organizationId]
  );

  const prepare = useCallback(async () => {
    if (!organizationId || !isModuleEnabled) {
      return null;
    }

    try {
      setLoading(true);
      setError("");

      const result = await fetchAndPersistOfflinePrepBundle({
        organizationId,
        userId: profile?.id ?? null,
      });
      return applyPrepResult(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "הכנה לא מקוון נכשלה"
      );
      return null;
    } finally {
      setLoading(false);
    }
  }, [organizationId, isModuleEnabled, profile?.id, projectId, applyPrepResult]);

  useEffect(() => {
    autoPrepareAttemptedRef.current = false;
  }, [organizationId, projectId]);

  useEffect(() => {
    if (!autoPrepare || !organizationId || !isModuleEnabled || !isOnline) {
      return;
    }
    if (hydrating || loading) {
      return;
    }
    if (isOfflinePrepValid(bundle)) {
      return;
    }
    if (autoPrepareAttemptedRef.current) {
      return;
    }

    autoPrepareAttemptedRef.current = true;
    void prepare();
  }, [
    autoPrepare,
    organizationId,
    isModuleEnabled,
    isOnline,
    hydrating,
    loading,
    bundle,
    prepare,
  ]);

  const cancel = useCallback(async () => {
    if (!organizationId || !isModuleEnabled) {
      return;
    }

    try {
      setCancelling(true);
      setError("");
      await clearOfflinePrepBundle(organizationId);
      setPreparedBundle(null);
      setStoredBundle(null);
      setImportSummary(null);
      clearOfflinePrepUiDismiss(organizationId);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "ביטול הכנה לא מקוון נכשל"
      );
    } finally {
      setCancelling(false);
    }
  }, [organizationId, isModuleEnabled]);

  return {
    bundle,
    isReady: isOfflinePrepValid(bundle),
    expiresAt: bundle?.expires_at || null,
    catalogVersion: bundle?.catalog_version || null,
    importSummary,
    loading: loading || hydrating,
    cancelling,
    error,
    prepare,
    cancel,
  };
}
