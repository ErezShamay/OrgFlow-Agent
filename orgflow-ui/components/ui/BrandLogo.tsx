"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function BrandLogo({
  size = "md",
  href = "/",
  showTagline = true,
}: {
  size?: "sm" | "md" | "lg";
  href?: string;
  showTagline?: boolean;
}) {
  const pathname = usePathname();

  const iconSize =
    size === "sm" ? "h-8 w-8 text-xs" : size === "lg" ? "h-12 w-12 text-base" : "h-10 w-10 text-sm";

  const titleSize =
    size === "sm" ? "text-base" : size === "lg" ? "text-2xl" : "text-lg";

  function handleClick(event: React.MouseEvent<HTMLAnchorElement>) {
    if (pathname !== href) {
      return;
    }

    event.preventDefault();
    window.history.replaceState(null, "", href);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <Link
      href={href}
      onClick={handleClick}
      className="group flex items-center gap-3"
      aria-label="Supervisor AI — דף הבית"
    >
      <div
        className={`
          flex
          shrink-0
          items-center
          justify-center
          rounded-xl
          bg-gradient-to-br
          from-blue-600
          to-violet-600
          font-black
          text-white
          shadow-lg
          shadow-blue-600/20
          transition-transform
          group-hover:scale-105
          ${iconSize}
        `}
      >
        SA
      </div>

      <div>
        <p className={`${titleSize} font-bold tracking-tight`}>
          Supervisor AI
        </p>

        {showTagline ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            שליטה ובקרה לפרויקטים
          </p>
        ) : null}
      </div>
    </Link>
  );
}
