"use client";

import type { ReactNode } from "react";

import { I18nProvider } from "@/providers/I18nProvider";
import { OfflineProvider } from "@/providers/OfflineProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import OfflineBanner from "@/components/ui/OfflineBanner";

export default function AppProviders({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <ThemeProvider>
      <I18nProvider>
        <OfflineProvider>
          <OfflineBanner />
          {children}
        </OfflineProvider>
      </I18nProvider>
    </ThemeProvider>
  );
}
