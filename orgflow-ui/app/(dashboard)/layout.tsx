import Sidebar from "@/app/components/sidebar";

import ContractorRouteGuard from "@/components/auth/ContractorRouteGuard";
import ResidentRouteGuard from "@/components/auth/ResidentRouteGuard";
import UserMenu from "@/components/auth/UserMenu";
import DashboardProviders from "@/components/dashboard/DashboardProviders";
import MobileNavMenu from "@/components/layout/MobileNavMenu";
import WorkspaceContextBar from "@/components/layout/WorkspaceContextBar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DashboardProviders>
    <div className="of-app-bg flex flex-col lg:min-h-screen lg:flex-row">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <header
          className="
            of-glass-header
            sticky
            top-0
            z-40
            flex
            h-auto
            min-h-[4.5rem]
            shrink-0
            items-center
            justify-between
            gap-3
            px-4
            py-3
            md:gap-4
            md:px-8
          "
        >
          <div className="flex min-w-0 flex-1 items-center gap-3 lg:contents">
            <MobileNavMenu />
            <WorkspaceContextBar />
          </div>
          <div className="shrink-0">
            <UserMenu />
          </div>
        </header>

        <main className="of-dashboard-main max-lg:flex-none max-lg:overflow-visible flex-1 overflow-auto">
          <ContractorRouteGuard>
            <ResidentRouteGuard>{children}</ResidentRouteGuard>
          </ContractorRouteGuard>
        </main>
      </div>
    </div>
    </DashboardProviders>
  );
}
