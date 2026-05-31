import type { ReactNode } from "react";

export default function PageShell({
  title,
  description,
  children,
  actions,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <main className="of-container py-6 text-zinc-900 md:py-10 dark:text-zinc-100">
      <div
        className="
          mb-8
          flex
          flex-col
          gap-4
          md:mb-10
          md:flex-row
          md:items-end
          md:justify-between
        "
      >
        <div>
          <h1 className="text-3xl font-bold md:text-5xl">
            {title}
          </h1>

          {description ? (
            <p className="mt-3 text-base text-zinc-600 md:text-lg dark:text-zinc-400">
              {description}
            </p>
          ) : null}
        </div>

        {actions ? (
          <div className="flex flex-wrap gap-3">{actions}</div>
        ) : null}
      </div>

      {children}
    </main>
  );
}
