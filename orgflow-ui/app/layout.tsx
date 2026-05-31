import type { Metadata } from "next";

import { Toaster } from "sonner";

import { AuthProvider } from "@/contexts/AuthContext";

import AuthGuard from "@/components/auth/AuthGuard";
import ErrorBoundary from "@/components/ui/ErrorBoundary";
import AppProviders from "@/providers/AppProviders";

import "./globals.css";

export const metadata: Metadata = {
  title: "Supervisor AI",
  description:
    "AI Operations Platform for Construction Management",
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
          bg-zinc-100
          dark:bg-zinc-950
          text-zinc-900
          dark:text-zinc-100
          antialiased
        "
      >

        <AppProviders>
          <AuthProvider>
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