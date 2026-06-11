import AdminGuard from "@/components/admin/AdminGuard";

export default function AutomationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AdminGuard>{children}</AdminGuard>;
}
