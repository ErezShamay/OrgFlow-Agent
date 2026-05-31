"use client";

import Link from "next/link";

import { usePathname } from "next/navigation";

export default function ProjectTabs({
  projectId,
}: {
  projectId: string;
}) {
  const pathname = usePathname();

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
      label: "נקודות סיכון",
      href: `/projects/${projectId}/escalations`,
    },
    {
      label: "פעולות",
      href: `/projects/${projectId}/actions`,
    },
  ];

  return (
    <div className="mb-10 flex flex-wrap gap-3">
      {tabs.map((tab) => {
        const isActive = pathname === tab.href;

        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={
              isActive
                ? "of-tab-link of-tab-link-active"
                : "of-tab-link of-tab-link-inactive"
            }
          >
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}
