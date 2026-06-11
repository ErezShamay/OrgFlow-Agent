"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type { FieldReportNetworkSnapshot } from "@/lib/field-reports/data-source";
import {
  probeFieldReportNetworkStatus,
  resolveFieldReportConnectivity,
  subscribeFieldReportNetworkStatus,
  type FieldReportNetworkConnectivity,
} from "@/lib/field-reports/sync/network-status";
import { useOffline } from "@/providers/OfflineProvider";

export type UseFieldReportNetworkStatusResult = {
  snapshot: FieldReportNetworkSnapshot;
  connectivity: FieldReportNetworkConnectivity;
  canSync: boolean;
  checking: boolean;
  refresh: () => Promise<void>;
};

/**
 * מצב רשת לדוחות שטח - ping ל-module-status + polling (FR-026).
 */
export function useFieldReportNetworkStatus(): UseFieldReportNetworkStatusResult {
  const { isOnline: navigatorOnline } = useOffline();
  const [snapshot, setSnapshot] = useState<FieldReportNetworkSnapshot>({
    navigatorOnline,
    apiReachable: false,
  });
  const [checking, setChecking] = useState(false);

  const refresh = useCallback(async () => {
    setChecking(true);
    try {
      setSnapshot(await probeFieldReportNetworkStatus());
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    setSnapshot((current) => ({
      ...current,
      navigatorOnline,
      apiReachable: navigatorOnline ? current.apiReachable : false,
    }));
  }, [navigatorOnline]);

  useEffect(() => {
    const unsubscribe = subscribeFieldReportNetworkStatus((next) => {
      setSnapshot(next);
    });

    return unsubscribe;
  }, []);

  const connectivity = useMemo(
    () => resolveFieldReportConnectivity(snapshot),
    [snapshot]
  );

  const canSync = snapshot.navigatorOnline && snapshot.apiReachable;

  return {
    snapshot,
    connectivity,
    canSync,
    checking,
    refresh,
  };
}
