"use client";

import { useEffect, useState } from "react";

/** Tailwind `lg` breakpoint - overlays use full-screen sheet below this width. */
const LG_MAX_WIDTH_PX = 1023;

function useMatchesMaxWidth(maxWidthPx: number, active: boolean) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    if (!active) {
      setMatches(false);
      return;
    }

    const mq = window.matchMedia(`(max-width: ${maxWidthPx}px)`);
    const sync = () => setMatches(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, [active, maxWidthPx]);

  return matches;
}

function lockElementOverflow(element: HTMLElement | null) {
  if (!element) {
    return () => {};
  }

  const previous = element.style.overflow;
  element.style.overflow = "hidden";

  return () => {
    element.style.overflow = previous;
  };
}

/**
 * Locks dashboard background scroll while a full-screen overlay is open on
 * viewports below Tailwind `lg`. Uses `.of-dashboard-main` instead of
 * `document.body` so touch scrolling inside the overlay still works in
 * Capacitor / Android WebView.
 */
export function useLockBackgroundScrollWhileOverlay(open: boolean) {
  const belowLg = useMatchesMaxWidth(LG_MAX_WIDTH_PX, open);

  useEffect(() => {
    if (!open || !belowLg) {
      return;
    }

    const main = document.querySelector<HTMLElement>(".of-dashboard-main");
    return lockElementOverflow(main);
  }, [open, belowLg]);
}

/** @deprecated Prefer {@link useLockBackgroundScrollWhileOverlay} for mobile sheets. */
export function useLockBodyScroll(locked: boolean) {
  useEffect(() => {
    if (!locked) {
      return;
    }

    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previous;
    };
  }, [locked]);
}
