"use client";

import { useEffect, useState } from "react";

import {
  connectPortfolioLiveUpdates,
  type QualityPortfolioLiveSnapshot,
} from "@/lib/quality-issues/portfolio-live";

export type PortfolioLiveState = {
  snapshot: QualityPortfolioLiveSnapshot | null;
  isLive: boolean;
};

export function usePortfolioLiveUpdates(
  enabled: boolean
): PortfolioLiveState {
  const [snapshot, setSnapshot] =
    useState<QualityPortfolioLiveSnapshot | null>(null);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setSnapshot(null);
      setIsLive(false);
      return;
    }

    const connection = connectPortfolioLiveUpdates((nextSnapshot) => {
      setSnapshot(nextSnapshot);
      setIsLive(true);
    });

    return () => {
      connection.stop();
    };
  }, [enabled]);

  return { snapshot, isLive };
}
