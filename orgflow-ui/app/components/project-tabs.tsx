"use client";

import Link from "next/link";

import { usePathname } from "next/navigation";

import { getQCProjectNavLinks } from "@/lib/qc-navigation";

export default function ProjectTabs({
  projectId,
  role,
}: {
  projectId: string;
  role?: string | null;
}) {
  const pathname = usePathname();
  const tabs = getQCProjectNavLinks(projectId, role);

  return (
    <div className="mb-10 flex flex-wrap gap-3">
      {tabs.map((tab) => {
        const isActive =
          tab.href === `/projects/${projectId}`
            ? pathname === tab.href
            : pathname === tab.href || pathname.startsWith(`${tab.href}/`);

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
