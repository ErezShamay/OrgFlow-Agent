import type { ReactNode } from "react";

import Button from "@/components/ui/Button";

export default function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
}: {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: ReactNode;
}) {
  return (
    <div
      className="
        of-card
        of-card-p10
        flex
        min-h-48
        flex-col
        items-center
        justify-center
        border-dashed
        text-center
      "
      role="status"
    >
      {icon ? (
        <div className="mb-4 text-zinc-400">{icon}</div>
      ) : null}

      <h2 className="text-xl font-semibold">{title}</h2>

      {description ? (
        <p className="mt-2 max-w-md text-sm text-zinc-500">
          {description}
        </p>
      ) : null}

      {actionLabel && onAction ? (
        <div className="mt-6">
          <Button variant="accent" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
