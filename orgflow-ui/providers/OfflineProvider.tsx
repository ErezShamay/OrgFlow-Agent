"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

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
    const updateStatus = () => {
      const online = window.navigator.onLine;
      setIsOnline(online);

      if (!online) {
        setWasOffline(true);
      }
    };

    updateStatus();
    window.addEventListener("online", updateStatus);
    window.addEventListener("offline", updateStatus);

    return () => {
      window.removeEventListener("online", updateStatus);
      window.removeEventListener("offline", updateStatus);
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
