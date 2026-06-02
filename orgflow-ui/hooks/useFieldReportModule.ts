"use client";

import { startTransition, useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api/client";
import {
  clearFieldReportLocalState,
} from "@/lib/field-reports/module-local-state";

type ModuleStatus = {
  organization_id: string;
  is_enabled: boolean;
  storage_available?: boolean;
};

export function useFieldReportModule() {
  const [status, setStatus] = useState<ModuleStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await apiFetch("/field-reports/module-status");

      if (!response.ok) {
        throw new Error("טעינת סטטוס המודול נכשלה");
      }

      setStatus(await response.json());
    } catch (err: unknown) {
      setStatus(null);
      setError(
        err instanceof Error
          ? err.message
          : "טעינת סטטוס המודול נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    startTransition(() => {
      void load();
    });
  }, [load]);

  useEffect(() => {
    if (!status?.organization_id || status.is_enabled) {
      return;
    }

    // Keep re-enable flow clean (5.4): don't restore local drafts/state
    // after module was disabled by the supplier.
    clearFieldReportLocalState(status.organization_id);
  }, [status]);

  return {
    status,
    isEnabled: Boolean(status?.is_enabled),
    loading,
    error,
    reload: load,
  };
}
