"use client";

import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/lib/api/client";
import {
  importInProgressReportsFromOfflinePrep,
  type ImportInProgressReportsResult,
} from "@/lib/field-reports/import-in-progress-reports";
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
  refreshOpenIssuesCacheForOrganization,
} from "@/lib/quality-issues/open-issues-offline";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";

export function useFieldReportOfflinePrep() {
  const { status } = useFieldReportModule();
  const { profile } = useAuth();
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
    useState<ImportInProgressReportsResult | null>(null);

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

  const prepare = useCallback(async () => {
    if (!organizationId || !isModuleEnabled) {
      return null;
    }

    try {
      setLoading(true);
      setError("");

      const response = await apiFetch("/field-reports/offline-prep");

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(
          payload.error?.message
            || payload.message
            || "הכנה לא מקוון נכשלה"
        );
      }

      const payload = await response.json();
      const saved = await saveOfflinePrepBundle(organizationId, payload);
      const projectIds = (payload.projects ?? [])
        .map((project: { id?: string | null }) => project.id?.trim())
        .filter((projectId: string | undefined): projectId is string =>
          Boolean(projectId)
        );
      if (projectIds.length > 0 && saved.expires_at) {
        await refreshOpenIssuesCacheForOrganization({
          organizationId,
          projectIds,
          expiresAt: saved.expires_at,
        });
      }
      const imported = await importInProgressReportsFromOfflinePrep({
        organizationId,
        userId: profile?.id ?? null,
        prepReports: payload.reports ?? [],
      });
      setImportSummary(imported);
      setPreparedBundle({
        organizationId,
        bundle: saved,
      });
      setStoredBundle(saved);
      return saved;
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
  }, [organizationId, isModuleEnabled, profile?.id]);

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
