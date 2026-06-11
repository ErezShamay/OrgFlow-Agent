"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { ELAYOAI_APP_NAME, ELAYOAI_APP_TAGLINE } from "@/lib/elayoai/keys";

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
  const router = useRouter();

  const iconSize =
    size === "sm" ? "h-8 w-8 text-xs" : size === "lg" ? "h-12 w-12 text-base" : "h-10 w-10 text-sm";

  const titleSize =
    size === "sm" ? "text-base" : size === "lg" ? "text-2xl" : "text-lg";

  function handleClick(event: React.MouseEvent<HTMLAnchorElement>) {
    if (pathname === href) {
      event.preventDefault();
      window.history.replaceState(null, "", href);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    if (href === "/") {
      event.preventDefault();
      window.history.replaceState(null, "", "/");
      router.push("/");
    }
  }

  return (
    <Link
      href={href}
      scroll={false}
      onClick={handleClick}
      className="group flex items-center gap-3"
      aria-label={`${ELAYOAI_APP_NAME} - דף הבית`}
    >
      <div
        className={`
          flex
          shrink-0
          items-center
          justify-center
          rounded-xl
          bg-gradient-to-br
          from-brand
          to-brand-gold
          font-black
          text-white
          shadow-lg
          shadow-brand/20
          transition-transform
          group-hover:scale-105
          ${iconSize}
        `}
      >
        El
      </div>

      <div>
        <p className={`${titleSize} font-bold tracking-tight`}>
          {ELAYOAI_APP_NAME}
        </p>

        {showTagline ? (
          <p className="text-xs text-[var(--of-color-text-muted)]">
            {ELAYOAI_APP_TAGLINE}
          </p>
        ) : null}
      </div>
    </Link>
  );
}
