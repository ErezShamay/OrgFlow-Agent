import type { ReactNode } from "react";

type KpiCardVariant = "default" | "warning" | "accent";

export default function KpiCard({
  label,
  value,
  variant = "default",
  className = "",
}: {
  label: string;
  value: ReactNode;
  variant?: KpiCardVariant;
  className?: string;
}) {
  const variantBorder =
    variant === "warning"
      ? "border-orange-200 dark:border-orange-900/60"
      : variant === "accent"
        ? "border-blue-200 dark:border-blue-900/60"
        : "";

  const labelClass =
    variant === "warning"
      ? "text-orange-500"
      : variant === "accent"
        ? "text-blue-600 dark:text-blue-400"
        : "";

  const isLargeValue =
    typeof value === "string" && value.length <= 4;

  return (
    <div className={`of-kpi-card ${variantBorder} ${className}`}>
      <p className={`of-kpi-label ${labelClass}`}>
        {label}
      </p>

      <div className={isLargeValue ? "of-kpi-value" : "of-kpi-value-sm"}>
        {value}
      </div>
    </div>
  );
}
