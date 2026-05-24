import Sidebar from "@/app/components/sidebar";

export default function ProjectsLayout({
  children,
}: {
  children: React.ReactNode;
}) {

  return (
    <div
      className="
        flex
        min-h-screen
        bg-zinc-100
        dark:bg-zinc-950
      "
    >

      <Sidebar />

      <main className="flex-1">
        {children}
      </main>

    </div>
  );
}