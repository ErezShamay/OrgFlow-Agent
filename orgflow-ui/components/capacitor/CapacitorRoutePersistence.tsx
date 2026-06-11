"use client";

import { useEffect, useRef } from "react";

import { usePathname, useSearchParams } from "next/navigation";

import { canUseCapacitorWebStorage } from "@/lib/capacitor/platform";
import {
  restoreCapacitorRouteIfNeeded,
  writeCapacitorPersistedRoute,
} from "@/lib/capacitor/route-persistence";

function buildPersistedPath(
  pathname: string,
  searchParams: URLSearchParams
): string {
  const query = searchParams.toString();
  return query ? `${pathname}?${query}` : pathname;
}

/**
 * שומר נתיב דוח ב-localStorage; שחזור אחרי מצלמה נעשה בסקריפט לפני React
 * או ב-visibilitychange (ניווט יחיד).
 */
export default function CapacitorRoutePersistence() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const resumeRestoreAttempted = useRef(false);

  useEffect(() => {
    if (!canUseCapacitorWebStorage() || !pathname) {
      return;
    }

    if (pathname.startsWith("/field-reports")) {
      writeCapacitorPersistedRoute(
        buildPersistedPath(pathname, searchParams)
      );
    }
  }, [pathname, searchParams]);

  useEffect(() => {
    if (!canUseCapacitorWebStorage()) {
      return;
    }

    const onVisible = () => {
      if (document.visibilityState !== "visible") {
        return;
      }

      if (resumeRestoreAttempted.current) {
        return;
      }

      resumeRestoreAttempted.current = true;
      restoreCapacitorRouteIfNeeded();
    };

    document.addEventListener("visibilitychange", onVisible);
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  return null;
}

/** לפני מצלמה / גלריה - חובה לשמור נתיב לשחזור אחרי יציאה לאפליקציית המצלמה. */
export function persistCapacitorRouteNow(): void {
  if (typeof window === "undefined") {
    return;
  }

  writeCapacitorPersistedRoute(
    `${window.location.pathname}${window.location.search}`
  );
}
