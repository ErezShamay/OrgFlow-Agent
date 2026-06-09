"use client";

import type { ReactNode } from "react";

import { FieldReportModuleProvider } from "@/contexts/FieldReportModuleContext";
import { FieldReportSyncContextProvider } from "@/contexts/FieldReportSyncContext";

export default function DashboardProviders({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <FieldReportModuleProvider>
      <FieldReportSyncContextProvider>{children}</FieldReportSyncContextProvider>
    </FieldReportModuleProvider>
  );
}
