"use client";

import { useEffect } from "react";

function isStandaloneDisplayMode() {
  return (
    window.matchMedia("(display-mode: standalone)").matches
    // iOS fallback
    || (window.navigator as Navigator & { standalone?: boolean }).standalone
      === true
  );
}

export default function PwaRegistration() {
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
      return;
    }

    let reloadingForUpdate = false;

    const safeReload = () => {
      if (reloadingForUpdate) {
        return;
      }
      reloadingForUpdate = true;
      window.location.reload();
    };

    const tryActivateWaitingWorker = (
      registration: ServiceWorkerRegistration
    ) => {
      if (!window.navigator.onLine) {
        return;
      }
      if (registration.waiting) {
        registration.waiting.postMessage({ type: "SKIP_WAITING" });
      }
    };

    const register = async () => {
      try {
        const registration = await navigator.serviceWorker.register("/sw.js", {
          scope: "/",
        });

        navigator.serviceWorker.addEventListener("controllerchange", () => {
          if (isStandaloneDisplayMode()) {
            safeReload();
          }
        });

        registration.addEventListener("updatefound", () => {
          const installing = registration.installing;
          if (!installing) {
            return;
          }

          installing.addEventListener("statechange", () => {
            if (installing.state === "installed") {
              tryActivateWaitingWorker(registration);
            }
          });
        });

        const refreshWhenOnline = () => {
          void registration.update();
          tryActivateWaitingWorker(registration);
        };
        window.addEventListener("online", refreshWhenOnline);

        return () => {
          window.removeEventListener("online", refreshWhenOnline);
        };
      } catch {
        // Keep app functional even if SW registration fails.
      }
    };

    let cleanup: (() => void) | undefined;
    void register().then((dispose) => {
      cleanup = dispose;
    });

    return () => {
      cleanup?.();
    };
  }, []);

  return null;
}
