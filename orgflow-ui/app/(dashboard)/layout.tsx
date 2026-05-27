import Sidebar from "@/app/components/sidebar";

import UserMenu from "@/components/auth/UserMenu";

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
        bg-zinc-50
        dark:bg-black
      "
    >

      <Sidebar />

      <div
        className="
          flex-1
          flex
          flex-col
        "
      >

        {/* HEADER */}

        <header
          className="
            h-20
            border-b
            border-zinc-200
            dark:border-zinc-800
            bg-white
            dark:bg-zinc-950
            px-8
            flex
            items-center
            justify-between
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

          <UserMenu />

        </header>

        {/* PAGE */}

        <main className="flex-1">

          {children}

        </main>

      </div>

    </div>
  );
}