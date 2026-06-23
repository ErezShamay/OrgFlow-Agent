"use client";

import { useParams } from "next/navigation";

import ProjectTradeDetailView from "@/components/projects/ProjectTradeDetailView";

export default function ProjectTradeDetailPage() {
  const params = useParams();
  const projectId = typeof params?.id === "string" ? params.id : "";
  const tradeKey = typeof params?.tradeKey === "string" ? params.tradeKey : "";

  if (!projectId || !tradeKey) {
    return (
      <main className="of-dashboard-page">
        <p>מלאכה לא נמצאה</p>
      </main>
    );
  }

  return (
    <main className="of-dashboard-page">
      <ProjectTradeDetailView projectId={projectId} tradeKey={tradeKey} />
    </main>
  );
}
