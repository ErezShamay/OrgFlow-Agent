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
import { TENANT_MANAGER_MODULE_CHANGED_EVENT } from "@/lib/tenant-manager/module-events";

type ModuleStatus = {
  organization_id: string;
  is_enabled: boolean;
  storage_available?: boolean;
};

type TenantManagerModuleContextValue = {
  status: ModuleStatus | null;
  isEnabled: boolean;
  loading: boolean;
  error: string;
  reload: () => Promise<void>;
};

const TenantManagerModuleContext =
  createContext<TenantManagerModuleContextValue | null>(null);

export function TenantManagerModuleProvider({
  children,
}: {
  children: ReactNode;
}) {
  const { currentOrgId, profile, loading: authLoading } = useAuth();
  const organizationIdHint =
    currentOrgId ?? profile?.organization_id ?? "";

  const [status, setStatus] = useState<ModuleStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organizationIdHint) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await apiFetch("/tenant-manager/module-status");

      if (!response.ok) {
        throw new Error("טעינת סטטוס מודול מנהל דיירים נכשלה");
      }

      const nextStatus = (await response.json()) as ModuleStatus;
      setStatus(nextStatus);
    } catch (err: unknown) {
      setStatus(null);
      setError(
        err instanceof Error
          ? err.message
          : "טעינת סטטוס מודול מנהל דיירים נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, [organizationIdHint]);

  useEffect(() => {
    if (!organizationIdHint) {
      setStatus(null);
      setLoading(authLoading);
      setError("");
      return;
    }

    setStatus(null);
    setLoading(true);
    setError("");
  }, [organizationIdHint, authLoading]);

  useEffect(() => {
    if (authLoading || !organizationIdHint) {
      return;
    }

    startTransition(() => {
      void load();
    });
  }, [authLoading, organizationIdHint, load]);

  useEffect(() => {
    function handleModuleChanged() {
      if (!organizationIdHint) {
        return;
      }

      startTransition(() => {
        void load();
      });
    }

    window.addEventListener(
      TENANT_MANAGER_MODULE_CHANGED_EVENT,
      handleModuleChanged
    );

    return () => {
      window.removeEventListener(
        TENANT_MANAGER_MODULE_CHANGED_EVENT,
        handleModuleChanged
      );
    };
  }, [load, organizationIdHint]);

  const value: TenantManagerModuleContextValue = {
    status,
    isEnabled: Boolean(status?.is_enabled),
    loading,
    error,
    reload: load,
  };

  return (
    <TenantManagerModuleContext.Provider value={value}>
      {children}
    </TenantManagerModuleContext.Provider>
  );
}

export function useTenantManagerModule(): TenantManagerModuleContextValue {
  const context = useContext(TenantManagerModuleContext);

  if (!context) {
    throw new Error(
      "useTenantManagerModule must be used within TenantManagerModuleProvider"
    );
  }

  return context;
}
