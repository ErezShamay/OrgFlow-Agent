import FieldReportSyncProvider from "@/components/field-reports/FieldReportSyncProvider";

export default function FieldReportsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="fr-field-reports min-h-full bg-zinc-50/50 dark:bg-zinc-950/40">
      <FieldReportSyncProvider>{children}</FieldReportSyncProvider>
    </div>
  );
}
