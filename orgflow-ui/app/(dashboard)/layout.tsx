import Sidebar from "@/app/components/sidebar";

import UserMenu from "@/components/auth/UserMenu";
import LocaleToggle from "@/components/ui/LocaleToggle";
import ThemeToggle from "@/components/ui/ThemeToggle";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {

  return (

    <div
      className="
        flex
        min-h-screen
        flex-col
        bg-zinc-50
        dark:bg-black
        lg:flex-row
      "
    >

      <Sidebar />

      <div
        className="
          flex
          min-w-0
          flex-1
          flex-col
        "
      >

        {/* HEADER */}

        <header
          className="
            flex
            h-auto
            min-h-20
            flex-wrap
            items-center
            justify-between
            gap-4
            border-b
            border-zinc-200
            bg-white
            px-4
            py-4
            dark:border-zinc-800
            dark:bg-zinc-950
            md:px-8
          "
        >

          <div>

            <h1
              className="
                text-xl
                font-bold
              "
            >
              Supervisor AI
            </h1>

            <p
              className="
                text-sm
                text-zinc-500
              "
            >
              AI Operational Platform
            </p>

          </div>

          <div className="flex flex-wrap items-center gap-2">
            <ThemeToggle />
            <LocaleToggle />
            <UserMenu />
          </div>

        </header>

        {/* PAGE */}

        <main className="flex-1">

          {children}

        </main>

      </div>

    </div>
  );
}