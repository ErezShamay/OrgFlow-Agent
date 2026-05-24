"use client";

import Link from "next/link";

import { usePathname } from "next/navigation";

export default function ProjectTabs({
  projectId,
}: {
  projectId: string;
}) {

  const pathname =
    usePathname();

  const tabs = [
    {
      label: "סקירה",
      href: `/projects/${projectId}`,
    },
    {
      label: "ביקורות AI",
      href: `/projects/${projectId}/reviews`,
    },
    {
      label: "הסלמות",
      href: `/projects/${projectId}/escalations`,
    },
    {
      label: "פעולות",
      href: `/projects/${projectId}/actions`,
    },
  ];

  return (
    <div
      className="
        flex
        gap-3
        mb-10
        flex-wrap
      "
    >

      {tabs.map((tab) => {

        const isActive =
          pathname === tab.href;

        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`
              px-5
              py-3
              rounded-2xl
              font-medium
              transition-all

              ${
                isActive
                  ? `
                    bg-zinc-900
                    text-white
                    dark:bg-white
                    dark:text-zinc-900
                  `
                  : `
                    bg-white
                    dark:bg-zinc-900
                    border
                    border-zinc-200
                    dark:border-zinc-800
                    hover:bg-zinc-100
                    dark:hover:bg-zinc-800
                  `
              }
            `}
          >
            {tab.label}
          </Link>
        );
      })}

    </div>
  );
}