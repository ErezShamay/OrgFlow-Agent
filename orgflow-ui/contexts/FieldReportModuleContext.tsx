"use client";

import {
  createContext,
  startTransition,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/lib/api/client";
import {
  clearCachedFieldReportModuleStatus,
  readCachedFieldReportModuleStatus,
  writeCachedFieldReportModuleStatus,
} from "@/lib/field-reports/module-status-cache";
import { clearFieldReportLocalState } from "@/lib/field-reports/module-local-state";

type ModuleStatus = {
  organization_id: string;
  is_enabled: boolean;
  storage_available?: boolean;
};

type FieldReportModuleContextValue = {
  status: ModuleStatus | null;
  isEnabled: boolean;
  loading: boolean;
  error: string;
  usingCachedStatus: boolean;
  reload: () => Promise<void>;
};

function moduleStatusFromCache(
  organizationId: string
): ModuleStatus | null {
  const cached = readCachedFieldReportModuleStatus(organizationId);
  if (!cached) {
    return null;
  }

  return {
    organization_id: cached.organization_id,
    is_enabled: cached.is_enabled,
    storage_available: cached.storage_available,
  };
}

const FieldReportModuleContext =
  createContext<FieldReportModuleContextValue | null>(null);

export function FieldReportModuleProvider({
  children,
}: {
  children: ReactNode;
}) {
  const { currentOrgId, profile } = useAuth();
  const organizationIdHint =
    currentOrgId ?? profile?.organization_id ?? "";
  const cachedStatus = organizationIdHint
    ? moduleStatusFromCache(organizationIdHint)
    : null;

  const [status, setStatus] = useState<ModuleStatus | null>(cachedStatus);
  const [loading, setLoading] = useState(!cachedStatus);
  const [error, setError] = useState("");
  const [usingCachedStatus, setUsingCachedStatus] = useState(
    Boolean(cachedStatus?.is_enabled)
  );

  const load = useCallback(async () => {
    const hasCachedStatus = Boolean(
      organizationIdHint
      && moduleStatusFromCache(organizationIdHint)
    );

    try {
      if (!hasCachedStatus) {
        setLoading(true);
      }

      setError("");
      setUsingCachedStatus(false);

      const response = await apiFetch("/field-reports/module-status");

      if (!response.ok) {
        throw new Error("טעינת סטטוס המודול נכשלה");
      }

      const nextStatus = (await response.json()) as ModuleStatus;
      setStatus(nextStatus);
      writeCachedFieldReportModuleStatus(nextStatus);

      if (!nextStatus.is_enabled) {
        clearCachedFieldReportModuleStatus(nextStatus.organization_id);
      }
    } catch (err: unknown) {
      const cachedStatus = organizationIdHint
        ? moduleStatusFromCache(organizationIdHint)
        : null;

      if (cachedStatus?.is_enabled) {
        setStatus(cachedStatus);
        setUsingCachedStatus(true);
        setError("");
      } else {
        setStatus(null);
        setError(
          err instanceof Error
            ? err.message
            : "טעינת סטטוס המודול נכשלה"
        );
      }
    } finally {
      setLoading(false);
    }
  }, [organizationIdHint]);

  useEffect(() => {
    const cached = organizationIdHint
      ? moduleStatusFromCache(organizationIdHint)
      : null;

    setStatus(cached);
    setLoading(!cached);
    setUsingCachedStatus(Boolean(cached?.is_enabled));
    setError("");
  }, [organizationIdHint]);

  useEffect(() => {
    startTransition(() => {
      void load();
    });
  }, [load]);

  useEffect(() => {
    if (!status?.organization_id || status.is_enabled) {
      return;
    }

    clearFieldReportLocalState(status.organization_id);
    clearCachedFieldReportModuleStatus(status.organization_id);
  }, [status]);

  const value: FieldReportModuleContextValue = {
    status,
    isEnabled: Boolean(status?.is_enabled),
    loading,
    error,
    usingCachedStatus,
    reload: load,
  };

  return (
    <FieldReportModuleContext.Provider value={value}>
      {children}
    </FieldReportModuleContext.Provider>
  );
}

export function useFieldReportModule(): FieldReportModuleContextValue {
  const context = useContext(FieldReportModuleContext);

  if (!context) {
    throw new Error(
      "useFieldReportModule must be used within FieldReportModuleProvider"
    );
  }

  return context;
}
