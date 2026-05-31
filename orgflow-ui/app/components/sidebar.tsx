"use client";

import Link from "next/link";
import {
  useParams,
  usePathname,
} from "next/navigation";

import BrandLogo from "@/components/ui/BrandLogo";
import NavLinkItem from "@/components/ui/NavLinkItem";
import { useIsAdmin } from "@/hooks/useEffectiveRole";
import {
  getSystemNavLinks,
  GLOBAL_NAV_LINKS,
  isNavLinkActive,
} from "@/lib/navigation";

export default function Sidebar() {
  const pathname = usePathname();
  const params = useParams();
  const isAdminUser = useIsAdmin();
  const projectId =
    typeof params?.id === "string"
      ? params.id
      : null;

  const systemLinks = getSystemNavLinks(isAdminUser);

  const projectLinks = projectId
    ? [
        {
          href: `/projects/${projectId}`,
          label: "סקירת הפרויקט",
        },
        {
          href: `/projects/${projectId}/reviews`,
          label: "ביקורות AI",
        },
        {
          href: `/projects/${projectId}/actions`,
          label: "פעולות תפעוליות",
        },
        {
          href: `/projects/${projectId}/escalations`,
          label: "נקודות סיכון",
        },
      ]
    : [];

  return (
    <aside
      className="
        of-glass-sidebar
        w-full
        border-b
        p-4
        lg:w-72
        lg:min-h-screen
        lg:border-b-0
        lg:border-l
        lg:p-6
      "
    >
      <div className="mb-10">
        <BrandLogo size="lg" />
      </div>

      <nav className="space-y-6">
        <div>
          <p
            className="
              mb-2
              px-4
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-zinc-400
            "
          >
            ניווט ראשי
          </p>

          <div className="space-y-1">
            {GLOBAL_NAV_LINKS.map((link) => (
              <NavLinkItem
                key={link.href}
                href={link.href}
                label={link.label}
                isActive={pathname === link.href}
              />
            ))}
          </div>
        </div>

        {projectLinks.length > 0 ? (
          <div>
            <p
              className="
                mb-2
                px-4
                text-xs
                font-semibold
                uppercase
                tracking-wide
                text-zinc-400
              "
            >
              פרויקט נוכחי
            </p>

            <div className="space-y-1">
              {projectLinks.map((link) => (
                <NavLinkItem
                  key={link.href}
                  href={link.href}
                  label={link.label}
                  isActive={pathname === link.href}
                />
              ))}
            </div>
          </div>
        ) : null}

        <div>
          <p
            className="
              mb-2
              px-4
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-zinc-400
            "
          >
            מערכת
          </p>

          <div className="space-y-1">
            {systemLinks.map((link) => (
              <NavLinkItem
                key={link.href}
                href={link.href}
                label={link.label}
                isActive={isNavLinkActive(pathname, link.href)}
              />
            ))}
          </div>
        </div>
      </nav>
    </aside>
  );
}
