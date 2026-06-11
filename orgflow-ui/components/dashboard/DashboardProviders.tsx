"use client";

import type { ReactNode } from "react";

import { FieldReportModuleProvider } from "@/contexts/FieldReportModuleContext";
import { FieldReportSyncContextProvider } from "@/contexts/FieldReportSyncContext";
import { TenantManagerModuleProvider } from "@/contexts/TenantManagerModuleContext";

export default function DashboardProviders({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <FieldReportModuleProvider>
      <TenantManagerModuleProvider>
        <FieldReportSyncContextProvider>
          {children}
        </FieldReportSyncContextProvider>
      </TenantManagerModuleProvider>
    </FieldReportModuleProvider>
  );
}
