import React from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "primary" | "success" | "warning" | "danger" | "neutral";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantClasses: Record<BadgeVariant, string> = {
  primary: "badge-primary",
  success: "badge-success",
  warning: "badge-warning",
  danger: "badge-danger",
  neutral: "badge bg-white/[0.08] text-white/50",
};

/**
 * Shared Badge primitive — wraps existing .badge-* CSS classes from index.css.
 * Use for status indicators, tags, and count pills.
 */
export function Badge({
  variant = "neutral",
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(variantClasses[variant], className)}
      {...props}
    >
      {children}
    </span>
  );
}
