"use client";

import type { ReactNode } from "react";

import { FieldReportModuleProvider } from "@/contexts/FieldReportModuleContext";

export default function DashboardProviders({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <FieldReportModuleProvider>{children}</FieldReportModuleProvider>
  );
}
