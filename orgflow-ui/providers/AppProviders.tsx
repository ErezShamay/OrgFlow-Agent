"use client";

import type { ReactNode } from "react";

import { I18nProvider } from "@/providers/I18nProvider";
import { OfflineProvider } from "@/providers/OfflineProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import PwaRegistration from "@/components/pwa/PwaRegistration";
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
          <PwaRegistration />
          <OfflineBanner />
          {children}
        </OfflineProvider>
      </I18nProvider>
    </ThemeProvider>
  );
}
