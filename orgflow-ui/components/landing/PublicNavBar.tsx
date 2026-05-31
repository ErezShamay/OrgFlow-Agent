"use client";

import Link from "next/link";

import BrandLogo from "@/components/ui/BrandLogo";
import LandingSectionLink from "@/components/ui/LandingSectionLink";
import SettingsNavLink from "@/components/ui/SettingsNavLink";
import {
  LANDING_SECTION_LINKS,
  SETTINGS_ROUTE,
} from "@/lib/navigation";

export default function PublicNavBar() {
  return (
    <header className="of-glass-header sticky top-0 z-50">
      <div
        className="
          of-container
          flex
          items-center
          justify-between
          gap-4
          py-4
        "
      >
        <BrandLogo />

        <nav
          className="
            hidden
            items-center
            gap-1
            md:flex
          "
          aria-label="ניווט ראשי"
        >
          {LANDING_SECTION_LINKS.map((link) => (
            <LandingSectionLink
              key={link.id}
              sectionId={link.id}
              label={link.label}
            />
          ))}

          <Link
            href={SETTINGS_ROUTE.href}
            className="
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
            "
          >
            {SETTINGS_ROUTE.label}
          </Link>
        </nav>

        <div className="flex shrink-0 items-center gap-2">
          <SettingsNavLink className="md:hidden" />

          <Link
            href="/auth/login"
            className="
              of-focus-ring
              inline-flex
              rounded-2xl
              bg-gradient-to-l
              from-blue-600
              to-violet-600
              px-4
              py-2.5
              text-sm
              font-semibold
              text-white
              shadow-md
              shadow-blue-600/20
              transition-all
              hover:brightness-110
              sm:px-5
            "
          >
            התחברות
          </Link>
        </div>
      </div>
    </header>
  );
}
