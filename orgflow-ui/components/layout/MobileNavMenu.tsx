"use client";

import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

import BrandLogo from "@/components/ui/BrandLogo";
import { useLockBackgroundScrollWhileOverlay } from "@/hooks/useLockBodyScroll";

import SidebarNavContent from "./SidebarNavContent";

export default function MobileNavMenu() {
  const [open, setOpen] = useState(false);

  useLockBackgroundScrollWhileOverlay(open);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  function closeMenu() {
    setOpen(false);
  }

  return (
    <>
      <button
        type="button"
        className="
          of-focus-ring
          inline-flex
          h-11
          w-11
          shrink-0
          items-center
          justify-center
          rounded-xl
          border
          border-zinc-200
          bg-white/90
          text-zinc-700
          transition
          hover:bg-zinc-50
          lg:hidden
          dark:border-zinc-700
          dark:bg-zinc-900/85
          dark:text-zinc-200
          dark:hover:bg-zinc-800
        "
        aria-label="פתח תפריט ניווט"
        aria-expanded={open}
        onClick={() => setOpen(true)}
      >
        <Menu className="h-5 w-5" />
      </button>

      {open ? (
        <>
          <div
            className="fixed inset-0 z-[60] bg-black/55 lg:hidden"
            role="presentation"
            onClick={closeMenu}
          />

          <aside
            className="
              fixed
              start-0
              top-0
              z-[70]
              flex
              h-dvh
              max-h-dvh
              w-72
              max-w-[85vw]
              flex-col
              overflow-y-auto
              overscroll-contain
              border-l
              border-zinc-200
              border-s-[3px]
              border-s-[var(--of-color-accent-secondary)]
              bg-white
              p-4
              shadow-2xl
              dark:border-zinc-700
              dark:bg-zinc-950
              lg:hidden
            "
            aria-label="תפריט ניווט"
          >
            <div className="mb-6 flex items-center justify-between gap-3">
              <BrandLogo size="lg" />
              <button
                type="button"
                className="
                  of-focus-ring
                  inline-flex
                  h-10
                  w-10
                  shrink-0
                  items-center
                  justify-center
                  rounded-xl
                  text-zinc-600
                  transition
                  hover:bg-zinc-100
                  dark:text-zinc-300
                  dark:hover:bg-zinc-800
                "
                aria-label="סגור תפריט ניווט"
                onClick={closeMenu}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <SidebarNavContent onLinkClick={closeMenu} />
          </aside>
        </>
      ) : null}
    </>
  );
}
