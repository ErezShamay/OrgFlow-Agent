"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";
import { FIELD_REPORTS_ROUTE, POST_LOGIN_ROUTE } from "@/lib/navigation";

type LandingSystemCtaVariant = "hero" | "footer";

const VARIANT_CLASS: Record<LandingSystemCtaVariant, string> = {
  hero: `
    of-focus-ring
    inline-flex
    items-center
    gap-2
    rounded-2xl
    bg-gradient-to-l
    from-brand
    to-brand-gold
    px-8
    py-4
    text-base
    font-semibold
    text-white
    shadow-lg
    shadow-brand/25
    transition-all
    hover:shadow-xl
    hover:shadow-brand/30
    hover:brightness-110
  `,
  footer: `
    of-focus-ring
    mt-8
    inline-flex
    items-center
    gap-2
    rounded-2xl
    bg-white
    px-8
    py-4
    text-base
    font-semibold
    text-zinc-900
    transition-all
    hover:bg-zinc-100
  `,
};

export default function LandingSystemCtaLink({
  variant,
  className = "",
}: {
  variant: LandingSystemCtaVariant;
  className?: string;
}) {
  const { user, loading } = useAuth();
  const isAuthenticated = !loading && Boolean(user);

  const { href, label } =
    variant === "hero"
      ? isAuthenticated
        ? {
            href: FIELD_REPORTS_ROUTE.href,
            label: "התחל דוח שטח",
          }
        : {
            href: "/auth/login",
            label: "כניסה למערכת",
          }
      : isAuthenticated
        ? {
            href: POST_LOGIN_ROUTE,
            label: "מעבר למערכת",
          }
        : {
            href: "/auth/login",
            label: "התחברות למערכת",
          };

  return (
    <Link
      href={href}
      className={`${VARIANT_CLASS[variant]} ${className}`.trim()}
    >
      {label}
      <ArrowLeft className="h-5 w-5" />
    </Link>
  );
}
