import Sidebar from "@/app/components/sidebar";

import UserMenu from "@/components/auth/UserMenu";
import OrgSwitcher from "@/components/admin/OrgSwitcher";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="of-app-bg flex min-h-screen flex-col lg:flex-row">
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
            flex-wrap
            items-center
            justify-end
            gap-4
            px-4
            py-3
            md:px-8
          "
        >
          <div className="flex flex-wrap items-center gap-2">
            <OrgSwitcher />
            <UserMenu />
          </div>
        </header>

        <main className="of-dashboard-main flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
