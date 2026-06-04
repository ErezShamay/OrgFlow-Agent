"use client";

import { useEffect, useRef } from "react";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { canUseCapacitorWebStorage } from "@/lib/capacitor/platform";
import {
  resolveCapacitorRestoreTarget,
  shouldRestoreCapacitorRoute,
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
 * שומר נתיב ב-APK (למקרה נדיר של reload). שחזור יחיד בלי reload מלא.
 */
export default function CapacitorRoutePersistence() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const restoredRef = useRef(false);

  useEffect(() => {
    if (!canUseCapacitorWebStorage() || !pathname) {
      return;
    }

    writeCapacitorPersistedRoute(
      buildPersistedPath(pathname, searchParams)
    );
  }, [pathname, searchParams]);

  useEffect(() => {
    if (!canUseCapacitorWebStorage() || restoredRef.current) {
      return;
    }

    if (!shouldRestoreCapacitorRoute(pathname)) {
      return;
    }

    const target = resolveCapacitorRestoreTarget();
    if (!target) {
      return;
    }

    restoredRef.current = true;
    router.replace(target);
  }, [pathname, router]);

  return null;
}

/** לפני פתיחת גלריה native — שמירת נתיב לשחזור אם נדרש. */
export function persistCapacitorRouteNow(): void {
  if (!canUseCapacitorWebStorage() || typeof window === "undefined") {
    return;
  }

  writeCapacitorPersistedRoute(
    `${window.location.pathname}${window.location.search}`
  );
}
