import Link from "next/link";

import { SETTINGS_ROUTE } from "@/lib/navigation";

export default function SettingsNavLink({
  className = "",
  variant = "button",
}: {
  className?: string;
  variant?: "button" | "text";
}) {
  if (variant === "text") {
    return (
      <Link
        href={SETTINGS_ROUTE.href}
        className={`
          text-sm
          font-medium
          text-zinc-600
          transition-colors
          hover:text-zinc-900
          dark:text-zinc-400
          dark:hover:text-zinc-100
          ${className}
        `}
      >
        {SETTINGS_ROUTE.label}
      </Link>
    );
  }

  return (
    <Link
      href={SETTINGS_ROUTE.href}
      className={`
        of-focus-ring
        inline-flex
        items-center
        rounded-2xl
        border
        border-zinc-200/80
        bg-white/90
        px-4
        py-2
        text-sm
        font-semibold
        text-zinc-900
        transition-colors
        hover:bg-zinc-50
        dark:border-zinc-700/80
        dark:bg-zinc-900/85
        dark:text-zinc-100
        dark:hover:bg-zinc-800
        ${className}
      `}
    >
      {SETTINGS_ROUTE.label}
    </Link>
  );
}
