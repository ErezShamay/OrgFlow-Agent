"use client";

import Link from "next/link";

import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";

export type ProjectOverviewListItem = {
  id: string;
  project_name: string;
  developer_name?: string | null;
  contractor_name?: string | null;
  lawyer_name?: string | null;
  supervisor_name: string;
  supervisor_email: string;
  status: string;
  created_at: string;
};

function displayStakeholder(value?: string | null) {
  const trimmed = value?.trim();
  return trimmed || "לא צוין";
}

function getStatusLabel(status: string) {
  switch (status) {
    case "ACTIVE":
      return "פעיל";
    case "COMPLETED":
      return "הושלם";
    default:
      return status;
  }
}

type ProjectOverviewListCardProps = {
  project: ProjectOverviewListItem;
  expanded: boolean;
  onToggleExpanded: () => void;
};

export default function ProjectOverviewListCard({
  project,
  expanded,
  onToggleExpanded,
}: ProjectOverviewListCardProps) {
  return (
    <Card>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold">
            {project.project_name}
          </h2>
        </div>

        <Badge variant="success">
          {getStatusLabel(project.status)}
        </Badge>
      </div>

      {expanded ? (
        <div className="mt-6 space-y-4 border-t border-zinc-200 pt-6 dark:border-zinc-700">
          <div>
            <h3 className="mb-2 font-semibold">יזם</h3>
            <p>{displayStakeholder(project.developer_name)}</p>
          </div>

          <div>
            <h3 className="mb-2 font-semibold">קבלן</h3>
            <p>{displayStakeholder(project.contractor_name)}</p>
          </div>

          <div>
            <h3 className="mb-2 font-semibold">עו״ד מלווה</h3>
            <p>{displayStakeholder(project.lawyer_name)}</p>
          </div>

          <div>
            <h3 className="mb-2 font-semibold">מפקח מלווה</h3>
            <p>{project.supervisor_name}</p>
          </div>

          <div>
            <h3 className="mb-2 font-semibold">אימייל מפקח מלווה</h3>
            <p>{project.supervisor_email || "-"}</p>
          </div>

          <div>
            <h3 className="mb-2 font-semibold">תאריך יצירה</h3>
            <p>
              {new Date(project.created_at).toLocaleDateString("he-IL")}
            </p>
          </div>

          <Link
            href={`/projects/${project.id}`}
            className="inline-flex text-sm font-medium text-brand hover:underline dark:text-brand-light"
          >
            מעבר לסקירת הפרויקט המלאה
          </Link>
        </div>
      ) : null}

      <div className="mt-6">
        <Button
          type="button"
          variant="secondary"
          onClick={onToggleExpanded}
        >
          {expanded ? "הצג פחות" : "הצג מידע נוסף"}
        </Button>
      </div>
    </Card>
  );
}
