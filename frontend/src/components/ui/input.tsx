import React from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
  wrapperClassName?: string;
}

/**
 * Shared Input primitive — wraps the existing `.input` CSS class from index.css.
 * Applies the consistent focus ring, border, bg, and placeholder treatment used app-wide.
 */
export function Input({
  label,
  error,
  leadingIcon,
  trailingIcon,
  wrapperClassName,
  className,
  id,
  ...props
}: InputProps) {
  const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className={cn("w-full", wrapperClassName)}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-medium text-white/40 mb-1.5"
        >
          {label}
        </label>
      )}
      <div className="relative">
        {leadingIcon && (
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none">
            {leadingIcon}
          </span>
        )}
        <input
          id={inputId}
          className={cn(
            "input",
            leadingIcon && "pl-10",
            trailingIcon && "pr-10",
            error && "border-danger/50 focus:border-danger/70 focus:ring-danger/20",
            className,
          )}
          {...props}
        />
        {trailingIcon && (
          <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none">
            {trailingIcon}
          </span>
        )}
      </div>
      {error && (
        <p className="mt-1 text-xs text-danger">{error}</p>
      )}
    </div>
  );
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  wrapperClassName?: string;
}

/**
 * Shared Textarea primitive — same visual treatment as Input.
 */
export function Textarea({
  label,
  error,
  wrapperClassName,
  className,
  id,
  ...props
}: TextareaProps) {
  const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className={cn("w-full", wrapperClassName)}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-medium text-white/40 mb-1.5"
        >
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        className={cn(
          "input resize-none",
          error && "border-danger/50 focus:border-danger/70",
          className,
        )}
        {...props}
      />
      {error && (
        <p className="mt-1 text-xs text-danger">{error}</p>
      )}
    </div>
  );
}
