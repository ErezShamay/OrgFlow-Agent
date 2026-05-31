"use client";

import Link from "next/link";
import {
  useParams,
  usePathname,
} from "next/navigation";

const GLOBAL_LINKS = [
  { href: "/", label: "דף הבית" },
  { href: "/portfolio", label: "תיק פרויקטים" },
  { href: "/projects", label: "פרויקטים" },
  { href: "/upload", label: "העלאת דוח" },
  { href: "/reviews", label: "ביקורות AI" },
  { href: "/actions", label: "פעולות תפעוליות" },
  { href: "/escalations", label: "נקודות סיכון" },
  { href: "/automation", label: "אוטומציה" },
  { href: "/automation/dead-letters", label: "Dead Letters" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const params = useParams();
  const projectId =
    typeof params?.id === "string"
      ? params.id
      : null;

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
        {
          href: `/projects/${projectId}/exceptions`,
          label: "חריגות",
        },
      ]
    : [];

  return (
    <aside
      className="
        w-full
        border-b
        border-zinc-200
        bg-white
        p-4
        dark:border-zinc-800
        dark:bg-zinc-900
        lg:w-72
        lg:min-h-screen
        lg:border-b-0
        lg:border-l
        lg:p-6
      "
    >
      <div className="mb-10">
        <Link href="/portfolio">
          <h1 className="cursor-pointer text-3xl font-bold">
            Supervisor AI
          </h1>
        </Link>

        <p
          className="
            mt-2
            text-zinc-500
            dark:text-zinc-400
          "
        >
          שליטה ובקרה לפרויקטים
        </p>
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

          <div className="space-y-2">
            {GLOBAL_LINKS.map((link) => (
              <NavLink
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

            <div className="space-y-2">
              {projectLinks.map((link) => (
                <NavLink
                  key={link.href}
                  href={link.href}
                  label={link.label}
                  isActive={pathname === link.href}
                />
              ))}
            </div>
          </div>
        ) : null}
      </nav>
    </aside>
  );
}

function NavLink({
  href,
  label,
  isActive,
}: {
  href: string;
  label: string;
  isActive: boolean;
}) {
  return (
    <Link
      href={href}
      className={`
        block
        rounded-2xl
        px-4
        py-3
        font-medium
        transition-colors
        ${
          isActive
            ? `
              bg-zinc-900
              text-white
              dark:bg-white
              dark:text-black
            `
            : `
              hover:bg-zinc-100
              dark:hover:bg-zinc-800
            `
        }
      `}
    >
      {label}
    </Link>
  );
}
