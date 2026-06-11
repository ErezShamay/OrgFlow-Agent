"use client";

import { usePathname } from "next/navigation";

import { useI18n } from "@/providers/I18nProvider";
import { useOffline } from "@/providers/OfflineProvider";

export default function OfflineBanner() {
  const pathname = usePathname();
  const { isOnline } = useOffline();
  const { t } = useI18n();

  if (isOnline) {
    return null;
  }

  const onFieldReports =
    pathname === "/field-reports"
    || pathname.startsWith("/field-reports/");

  return (
    <div
      role="alert"
      className="
        fixed
        inset-x-0
        top-0
        z-[var(--of-z-offline-banner)]
        bg-amber-500
        px-4
        py-2
        text-center
        text-sm
        font-medium
        text-amber-950
      "
    >
      {onFieldReports
        ? "אין רשת - דוחות שטח נשמרים במכשיר; המשך בדוח שפתחת."
        : t("common.offline")}
    </div>
  );
}
