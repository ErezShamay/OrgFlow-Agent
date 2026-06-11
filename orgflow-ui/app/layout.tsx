import type { Metadata } from "next";
import Script from "next/script";
import { Suspense } from "react";

import { ELAYOAI_APP_DESCRIPTION, ELAYOAI_APP_NAME } from "@/lib/elayoai/keys";
import { CAPACITOR_ROUTE_RESTORE_SCRIPT } from "@/lib/capacitor/route-restore-script";
import { THEME_INIT_SCRIPT } from "@/lib/theme/theme-init-script";
import { Toaster } from "sonner";

import { AuthProvider } from "@/contexts/AuthContext";

import AuthGuard from "@/components/auth/AuthGuard";
import CapacitorRoutePersistence from "@/components/capacitor/CapacitorRoutePersistence";
import ErrorBoundary from "@/components/ui/ErrorBoundary";
import AppProviders from "@/providers/AppProviders";

import "./globals.css";

export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover" as const,
};

export const metadata: Metadata = {
  title: ELAYOAI_APP_NAME,
  description: ELAYOAI_APP_DESCRIPTION,
  manifest: "/manifest.webmanifest",
  applicationName: ELAYOAI_APP_NAME,
  icons: {
    icon: [
      { url: "/icons/icon-192.svg", sizes: "192x192", type: "image/svg+xml" },
      { url: "/icons/icon-512.svg", sizes: "512x512", type: "image/svg+xml" },
    ],
    apple: [{ url: "/icons/icon-192.svg", type: "image/svg+xml" }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (

    <html
      lang="he"
      dir="rtl"
      suppressHydrationWarning
    >

      <body
        className="
          bg-[var(--of-color-surface-muted)]
          dark:bg-[var(--of-color-surface-muted)]
          text-[var(--of-color-text)]
          antialiased
        "
      >
        <Script id="elayoai-theme-init" strategy="beforeInteractive">
          {THEME_INIT_SCRIPT}
        </Script>
        <Script id="elayoai-capacitor-route-restore" strategy="beforeInteractive">
          {CAPACITOR_ROUTE_RESTORE_SCRIPT}
        </Script>
        <AppProviders>
          <AuthProvider>
            <Suspense fallback={null}>
              <CapacitorRoutePersistence />
            </Suspense>
            <AuthGuard>
              <ErrorBoundary>
                {children}
              </ErrorBoundary>

              <Toaster
                richColors
                position="top-left"
                closeButton
                style={{ zIndex: "var(--of-z-toast)" }}
              />
            </AuthGuard>
          </AuthProvider>
        </AppProviders>

      </body>

    </html>
  );
}