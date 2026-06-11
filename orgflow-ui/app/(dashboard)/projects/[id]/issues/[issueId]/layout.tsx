import { dashboardDynamicSegmentParams } from "@/lib/capacitor/static-export-params";

export function generateStaticParams() {
  return dashboardDynamicSegmentParams().map((params) => ({
    issueId: params.id,
  }));
}

export default function ProjectIssueDetailLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
