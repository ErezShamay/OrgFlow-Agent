"use client";

import {
  useEffect,
  useRef,
} from "react";

import {
  useRouter,
} from "next/navigation";

import { toast } from "sonner";

import {
  SESSION_IDLE_TIMEOUT_MS,
  SESSION_IDLE_TIMEOUT_MINUTES,
} from "@/lib/auth/session";

const ACTIVITY_THROTTLE_MS = 1000;

const ACTIVITY_EVENTS = [
  "mousedown",
  "keydown",
  "scroll",
  "touchstart",
  "click",
] as const;

export function useIdleSessionTimeout(
  enabled: boolean,
  onIdle: () => void | Promise<void>,
) {
  const router = useRouter();
  const onIdleRef = useRef(onIdle);
  const lastActivityRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const signingOutRef = useRef(false);

  onIdleRef.current = onIdle;

  useEffect(() => {
    if (!enabled) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }

      signingOutRef.current = false;
      return;
    }

    function clearScheduledLogout() {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    }

    async function performIdleSignOut() {
      if (signingOutRef.current) {
        return;
      }

      signingOutRef.current = true;
      clearScheduledLogout();

      try {
        await onIdleRef.current();
        toast.info(
          `הסשן נותק לאחר ${SESSION_IDLE_TIMEOUT_MINUTES} דקות של אי-פעילות`
        );
        router.replace("/");
      } catch {
        // onIdle נכשל או נחסם (למשל דוחות ממתינים לסנכרון) - נשארים מחוברים.
      } finally {
        signingOutRef.current = false;
      }
    }

    function scheduleLogout() {
      clearScheduledLogout();

      const elapsed = Date.now() - lastActivityRef.current;
      const remaining = Math.max(
        0,
        SESSION_IDLE_TIMEOUT_MS - elapsed
      );

      timeoutRef.current = setTimeout(() => {
        void performIdleSignOut();
      }, remaining);
    }

    function bumpActivity() {
      const now = Date.now();

      if (
        now - lastActivityRef.current
        < ACTIVITY_THROTTLE_MS
      ) {
        return;
      }

      lastActivityRef.current = now;
      scheduleLogout();
    }

    function handleVisibilityChange() {
      if (document.visibilityState !== "visible") {
        return;
      }

      const idleDuration =
        Date.now() - lastActivityRef.current;

      if (idleDuration >= SESSION_IDLE_TIMEOUT_MS) {
        void performIdleSignOut();
        return;
      }

      scheduleLogout();
    }

    lastActivityRef.current = Date.now();
    scheduleLogout();

    for (const event of ACTIVITY_EVENTS) {
      window.addEventListener(
        event,
        bumpActivity,
        { passive: true }
      );
    }

    document.addEventListener(
      "visibilitychange",
      handleVisibilityChange
    );

    return () => {
      clearScheduledLogout();

      for (const event of ACTIVITY_EVENTS) {
        window.removeEventListener(
          event,
          bumpActivity
        );
      }

      document.removeEventListener(
        "visibilitychange",
        handleVisibilityChange
      );
    };
  }, [enabled, router]);
}
