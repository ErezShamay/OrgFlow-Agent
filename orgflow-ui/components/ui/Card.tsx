import type { ReactNode } from "react";

export default function Card({
  children,
  className = "",
  padding = "lg",
  interactive = false,
  muted = false,
}: {
  children: ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg" | "xl";
  interactive?: boolean;
  muted?: boolean;
}) {
  const paddingClass =
    padding === "sm"
      ? "of-card-p6"
      : padding === "md"
        ? "of-card-p6"
        : padding === "xl"
          ? "of-card-p10 of-card-xl"
          : "of-card-p8";

  return (
    <div
      className={`
        of-card
        ${paddingClass}
        ${interactive ? "of-card-interactive" : ""}
        ${muted ? "of-card-muted" : ""}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
