"use client";

import {
  useEffect,
} from "react";

import {
  useRouter,
} from "next/navigation";

import AppLoadingScreen from "@/components/ui/AppLoadingScreen";
import {
  useAuth,
} from "@/contexts/AuthContext";
import {
  useIsPlatformAdmin,
} from "@/hooks/useEffectiveRole";

export default function PlatformAdminGuard({
  children,
}: {
  children: React.ReactNode;
}) {
  const { loading } = useAuth();
  const isPlatformAdminUser = useIsPlatformAdmin();
  const router = useRouter();

  useEffect(() => {
    if (loading) {
      return;
    }

    if (!isPlatformAdminUser) {
      router.replace("/");
    }
  }, [loading, isPlatformAdminUser, router]);

  if (loading) {
    return <AppLoadingScreen />;
  }

  if (!isPlatformAdminUser) {
    return null;
  }

  return <>{children}</>;
}
