import type { ReactNode } from "react";

import PageHeader from "@/components/ui/PageHeader";

export default function PageShell({
  title,
  description,
  eyebrow,
  children,
  actions,
}: {
  title: string;
  description?: string;
  eyebrow?: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="of-dashboard-page of-container">
      <PageHeader
        title={title}
        description={description}
        eyebrow={eyebrow}
        actions={actions}
      />

      {children}
    </div>
  );
}
