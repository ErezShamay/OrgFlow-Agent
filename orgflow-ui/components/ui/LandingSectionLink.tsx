"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { landingSectionHref } from "@/lib/navigation";

function scrollToSection(sectionId: string) {
  window.history.replaceState(null, "", landingSectionHref(sectionId));
  document.getElementById(sectionId)?.scrollIntoView({
    behavior: "smooth",
  });
}

export default function LandingSectionLink({
  sectionId,
  label,
  className = "",
}: {
  sectionId: string;
  label: string;
  className?: string;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const href = landingSectionHref(sectionId);

  function handleClick(event: React.MouseEvent<HTMLAnchorElement>) {
    if (pathname === "/") {
      event.preventDefault();
      scrollToSection(sectionId);
      return;
    }

    event.preventDefault();
    router.push(href);
  }

  return (
    <Link
      href={href}
      onClick={handleClick}
      className={`
        rounded-xl
        px-4
        py-2
        text-sm
        font-medium
        text-zinc-600
        transition-colors
        hover:bg-zinc-100
        hover:text-zinc-900
        dark:text-zinc-400
        dark:hover:bg-zinc-800
        dark:hover:text-zinc-100
        ${className}
      `}
    >
      {label}
    </Link>
  );
}
