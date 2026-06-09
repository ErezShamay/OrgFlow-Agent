"use client";

import type { ReactNode } from "react";

import SyncPanel from "@/components/field-reports/SyncPanel";

/** מציג את פאנל ההעלאה בתוך מודול דוחות שטח (הסנכרון רץ מ-DashboardProviders). */
export default function FieldReportSyncProvider({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <>
      <SyncPanel />
      {children}
    </>
  );
}
