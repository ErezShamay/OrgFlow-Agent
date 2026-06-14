"use client";

import Link from "next/link";

import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { projectFieldReportNewPath } from "@/lib/field-reports/routes";
import { FR_PRIMARY_ACTION_BUTTON } from "@/lib/field-reports/touch-input-class";

export default function ProjectFieldReportLink({
  projectId,
}: {
  projectId: string;
}) {
  const { isEnabled, loading } = useFieldReportModule();

  if (loading || !isEnabled) {
    return null;
  }

  return (
    <Link
      href={projectFieldReportNewPath(projectId)}
      className={FR_PRIMARY_ACTION_BUTTON}
    >
      הפקת דוח
    </Link>
  );
}
