"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useFieldReportOfflinePrep } from "@/hooks/useFieldReportOfflinePrep";
import { useOffline } from "@/providers/OfflineProvider";

/**
 * באנר אופליין בהקשר דוחות שטח - משלים את `OfflineBanner` הגלובלי (§6 ב.8).
 */
export default function FieldReportsOfflineBanner() {
  const pathname = usePathname();
  const { isOnline } = useOffline();
  const offlinePrep = useFieldReportOfflinePrep();

  const onFieldReports =
    pathname === "/field-reports"
    || pathname.startsWith("/field-reports/");

  if (!onFieldReports || isOnline) {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className="border-b border-amber-300 bg-amber-50 px-4 py-2.5 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-100"
    >
      <p>
        <strong>אין רשת</strong> - עריכת דוחות ומפרט מהנתונים במכשיר.
        {offlinePrep.isReady
          ? " ההכנה לא מקוון בתוקף."
          : " בצע «הכנה לא מקוון» כשתחזור רשת."}
      </p>
      {!offlinePrep.isReady ? (
        <p className="mt-1 text-xs">
          <Link href="/field-reports" className="font-medium underline">
            חזור להפקת דוחות
          </Link>
          {" "}להפעלת הכנה.
        </p>
      ) : null}
    </div>
  );
}
