import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "glass" | "icon" | "danger" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leadingIcon?: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: "btn-primary",
  glass: "btn-glass",
  icon: "btn-icon",
  danger:
    "flex items-center justify-center gap-2 rounded-xl border border-danger/30 bg-danger/10 px-4 py-2.5 text-sm font-medium text-danger backdrop-blur-sm transition-all duration-200 hover:bg-danger/20 hover:border-danger/50 select-none",
  ghost:
    "flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium text-white/40 transition-all duration-200 hover:text-white hover:bg-white/[0.04] select-none",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2.5 text-sm",
  lg: "px-6 py-3 text-base",
};

/**
 * Shared Button primitive — wraps existing CSS component classes from index.css.
 * All variants automatically include hover, focus-visible, active, disabled, and loading states.
 */
export function Button({
  variant = "glass",
  size = "md",
  isLoading = false,
  disabled,
  leadingIcon,
  children,
  className,
  ...props
}: ButtonProps) {
  const base = variantClasses[variant];

  // For icon variant, size override doesn't apply (icon buttons have fixed padding)
  const sizeOverride = variant !== "icon" && variant !== "primary" && variant !== "glass" ? sizeClasses[size] : "";

  return (
    <button
      {...props}
      disabled={disabled || isLoading}
      className={cn(base, sizeOverride, isLoading && "cursor-wait", className)}
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin shrink-0" />
      ) : leadingIcon ? (
        <span className="shrink-0">{leadingIcon}</span>
      ) : null}
      {children}
    </button>
  );
}
