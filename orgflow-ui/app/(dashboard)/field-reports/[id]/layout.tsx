import { dashboardDynamicSegmentParams } from "@/lib/capacitor/static-export-params";

export function generateStaticParams() {
  return dashboardDynamicSegmentParams();
}

export default function FieldReportIdLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
