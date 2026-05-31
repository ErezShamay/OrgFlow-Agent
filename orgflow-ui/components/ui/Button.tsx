"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant =
  | "primary"
  | "secondary"
  | "ghost"
  | "danger"
  | "accent";

type ButtonSize = "sm" | "md" | "lg";

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-brand text-white hover:bg-brand-dark dark:bg-brand-light dark:text-brand-dark dark:hover:bg-brand",
  secondary:
    "border border-zinc-200/80 bg-white/90 text-zinc-900 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900/85 dark:text-zinc-100 dark:hover:bg-zinc-800",
  ghost:
    "bg-transparent hover:bg-zinc-100 dark:hover:bg-zinc-800",
  danger:
    "bg-red-600 text-white hover:bg-red-700",
  accent:
    "bg-gradient-to-l from-brand to-brand-gold text-white shadow-lg shadow-brand/20 hover:brightness-110",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-sm rounded-xl",
  md: "px-4 py-2 text-sm rounded-2xl",
  lg: "px-6 py-3 text-base rounded-2xl",
};

export default function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
}) {
  return (
    <button
      type={type}
      className={`
        of-focus-ring
        inline-flex
        items-center
        justify-center
        font-semibold
        transition-all
        disabled:cursor-not-allowed
        disabled:opacity-50
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}
