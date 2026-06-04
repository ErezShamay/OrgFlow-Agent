"use client";

import { useEffect, useLayoutEffect, useRef } from "react";

import { App } from "@capacitor/app";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useAuth } from "@/contexts/AuthContext";
import {
  canUseCapacitorWebStorage,
  isCapacitorNativePlatform,
} from "@/lib/capacitor/platform";
import {
  currentDocumentPath,
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

function navigateToRestoreTarget(
  target: string,
  router: ReturnType<typeof useRouter>
) {
  if (currentDocumentPath() === target) {
    return;
  }

  if (canUseCapacitorWebStorage()) {
    window.location.replace(target);
    return;
  }

  router.replace(target);
}

function tryRestoreRoute(
  pathname: string,
  router: ReturnType<typeof useRouter>
): boolean {
  if (!shouldRestoreCapacitorRoute(pathname)) {
    return false;
  }

  const target = resolveCapacitorRestoreTarget();
  if (!target) {
    return false;
  }

  navigateToRestoreTarget(target, router);
  return true;
}

/**
 * שומר את הנתיב הנוכחי ב-APK ומשחזר אחרי reload (למשל אחרי Camera).
 */
export default function CapacitorRoutePersistence() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, loading } = useAuth();
  const restoredRef = useRef(false);

  useLayoutEffect(() => {
    if (!canUseCapacitorWebStorage() || !pathname) {
      return;
    }

    tryRestoreRoute(pathname, router);
  }, [pathname, router]);

  useEffect(() => {
    if (!canUseCapacitorWebStorage() || !pathname) {
      return;
    }

    writeCapacitorPersistedRoute(
      buildPersistedPath(pathname, searchParams)
    );
  }, [pathname, searchParams]);

  useEffect(() => {
    if (!isCapacitorNativePlatform()) {
      return;
    }

    const attachResumeRestore = async () => {
      const handles = await Promise.all([
        App.addListener("appStateChange", ({ isActive }) => {
          if (!isActive) {
            return;
          }

          tryRestoreRoute(window.location.pathname, router);
        }),
        App.addListener("resume", () => {
          tryRestoreRoute(window.location.pathname, router);
        }),
      ]);

      return () => {
        for (const handle of handles) {
          void handle.remove();
        }
      };
    };

    let cleanup: (() => void) | undefined;
    void attachResumeRestore().then((dispose) => {
      cleanup = dispose;
    });

    return () => {
      cleanup?.();
    };
  }, [router]);

  useEffect(() => {
    if (
      !canUseCapacitorWebStorage()
      || loading
      || !user
      || restoredRef.current
    ) {
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
    navigateToRestoreTarget(target, router);
  }, [loading, user, pathname, router]);

  return null;
}

/** לפני פתיחת מצלמה/גלריה — מבטיח שיש נתיב לשחזור. */
export function persistCapacitorRouteNow(): void {
  if (!canUseCapacitorWebStorage()) {
    return;
  }

  writeCapacitorPersistedRoute(currentDocumentPath());
}
