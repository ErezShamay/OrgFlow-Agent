"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import LoadingState from "@/components/ui/LoadingState";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import {
  canContractorAccessRoute,
  contractorDeniedRouteRedirect,
} from "@/lib/auth/contractor-route-guard";

type ContractorRouteGuardProps = {
  children: React.ReactNode;
};

export default function ContractorRouteGuard({
  children,
}: ContractorRouteGuardProps) {
  const pathname = usePathname();
  const router = useRouter();
  const role = useEffectiveRole();
  const allowed = canContractorAccessRoute(role, pathname);

  useEffect(() => {
    if (!allowed) {
      router.replace(contractorDeniedRouteRedirect(role));
    }
  }, [allowed, role, router]);

  if (!allowed) {
    return (
      <div className="of-dashboard-page">
        <LoadingState message="מעביר לתצוגת ליקויים..." />
      </div>
    );
  }

  return <>{children}</>;
}
