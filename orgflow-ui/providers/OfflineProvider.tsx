"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  refreshCapacitorNetworkStatus,
  subscribeCapacitorNetworkConnectivity,
  isCapacitorFieldReportNetwork,
} from "@/lib/capacitor/field-report-network";

type OfflineContextValue = {
  isOnline: boolean;
  wasOffline: boolean;
};

const OfflineContext = createContext<OfflineContextValue | null>(
  null
);

export function OfflineProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [isOnline, setIsOnline] = useState(true);
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    const applyOnline = (online: boolean) => {
      setIsOnline(online);

      if (!online) {
        setWasOffline(true);
      }
    };

    const updateFromNavigator = () => {
      applyOnline(window.navigator.onLine);
    };

    if (isCapacitorFieldReportNetwork()) {
      void refreshCapacitorNetworkStatus().then(applyOnline);

      const unsubscribe = subscribeCapacitorNetworkConnectivity(applyOnline);
      return unsubscribe;
    }

    updateFromNavigator();
    window.addEventListener("online", updateFromNavigator);
    window.addEventListener("offline", updateFromNavigator);

    return () => {
      window.removeEventListener("online", updateFromNavigator);
      window.removeEventListener("offline", updateFromNavigator);
    };
  }, []);

  const value = useMemo(
    () => ({ isOnline, wasOffline }),
    [isOnline, wasOffline]
  );

  return (
    <OfflineContext.Provider value={value}>
      {children}
    </OfflineContext.Provider>
  );
}

export function useOffline() {
  const context = useContext(OfflineContext);

  if (!context) {
    throw new Error(
      "useOffline must be used within OfflineProvider"
    );
  }

  return context;
}
