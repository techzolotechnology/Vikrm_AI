import React from "react";
import { cn } from "@/lib/utils";

type CardVariant = "default" | "hover" | "elevated";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  as?: React.ElementType;
}

const variantClasses: Record<CardVariant, string> = {
  default: "glass-card",
  hover: "glass-card-hover",
  elevated: "glass-card-elevated",
};

/**
 * Shared Card primitive — wraps .glass-card / .glass-card-hover / .glass-card-elevated from index.css.
 * Use variant="hover" for clickable cards (applies the lift + glow on hover).
 * Use variant="elevated" for modal-style panels that sit above the page.
 */
export function Card({
  variant = "default",
  as: Component = "div",
  className,
  children,
  ...props
}: CardProps) {
  return (
    <Component
      className={cn(variantClasses[variant], className)}
      {...props}
    >
      {children}
    </Component>
  );
}
