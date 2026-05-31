"use client";

import { useEffect } from "react";

import { usePathname } from "next/navigation";

export default function LandingHashScroll() {
  const pathname = usePathname();

  useEffect(() => {
    if (pathname !== "/") {
      return;
    }

    function scrollToHash() {
      const hash = window.location.hash;

      if (!hash.startsWith("#")) {
        return;
      }

      const sectionId = hash.slice(1);

      const attempt = (retriesLeft = 12) => {
        const element = document.getElementById(sectionId);

        if (element) {
          element.scrollIntoView({ behavior: "smooth" });
          return;
        }

        if (retriesLeft > 0) {
          window.setTimeout(() => attempt(retriesLeft - 1), 50);
        }
      };

      requestAnimationFrame(() => attempt());
    }

    scrollToHash();
    window.addEventListener("hashchange", scrollToHash);

    return () => {
      window.removeEventListener("hashchange", scrollToHash);
    };
  }, [pathname]);

  return null;
}
