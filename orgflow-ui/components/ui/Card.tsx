import type { ReactNode } from "react";

export default function Card({
  children,
  className = "",
  padding = "lg",
}: {
  children: ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg";
}) {
  const paddingClass =
    padding === "sm"
      ? "p-4"
      : padding === "md"
        ? "p-6"
        : "p-8";

  return (
    <div
      className={`
        rounded-3xl
        border
        border-zinc-200
        bg-white
        shadow-sm
        dark:border-zinc-800
        dark:bg-zinc-900
        ${paddingClass}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
