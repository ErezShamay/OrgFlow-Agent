import type { ReactNode } from "react";

export default function PageHeader({
  title,
  description,
  eyebrow,
  actions,
  className = "",
}: {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`
        mb-8
        flex
        flex-col
        gap-4
        md:mb-10
        md:flex-row
        md:items-end
        md:justify-between
        ${className}
      `}
    >
      <div>
        {eyebrow ? (
          <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
            {eyebrow}
          </p>
        ) : null}

        <h1 className="of-page-title">
          {title}
        </h1>

        {description ? (
          <p className="of-page-desc">
            {description}
          </p>
        ) : null}
      </div>

      {actions ? (
        <div className="flex flex-wrap gap-3">
          {actions}
        </div>
      ) : null}
    </div>
  );
}
