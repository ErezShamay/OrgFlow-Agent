import type { ReactNode } from "react";

type BadgeVariant =
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral";

export default function Badge({
  children,
  variant = "neutral",
  className = "",
}: {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}) {
  const variantClass = {
    success: "of-badge-success",
    warning: "of-badge-warning",
    danger: "of-badge-danger",
    info: "of-badge-info",
    neutral: "of-badge-neutral",
  }[variant];

  return (
    <span className={`of-badge ${variantClass} ${className}`}>
      {children}
    </span>
  );
}
