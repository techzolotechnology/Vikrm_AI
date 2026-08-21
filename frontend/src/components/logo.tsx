import { cn } from "@/lib/utils";

interface ZyntrixLogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  useImage?: boolean;
  useLockup?: boolean;
  showText?: boolean;
  showTagline?: boolean;
  className?: string;
  textClassName?: string;
}

export function ZyntrixLogo({
  size = "md",
  useImage = false,
  useLockup = false,
  showText = true,
  showTagline = false,
  className,
  textClassName,
}: ZyntrixLogoProps) {
  const iconDimensions = {
    sm: "h-8 w-8",
    md: "h-9 w-9",
    lg: "h-12 w-12",
    xl: "h-16 w-16",
  }[size];

  const lockupHeights = {
    sm: "h-7",
    md: "h-9",
    lg: "h-12",
    xl: "h-16",
  }[size];

  const textSizes = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-xl",
    xl: "text-2xl",
  }[size];

  if (useLockup) {
    return (
      <img
        src="/zyntrix-lockup.png"
        alt="Zyntrix AI"
        className={cn(lockupHeights, "object-contain", className)}
      />
    );
  }

  if (useImage) {
    return (
      <img
        src="/zyntrix-logo.png"
        alt="Zyntrix AI"
        className={cn(lockupHeights, "object-contain", className)}
      />
    );
  }

  return (
    <div className={cn("inline-flex items-center gap-3 select-none", className)}>
      {/* Logo Graphic Mark */}
      <div className={cn("relative shrink-0 flex items-center justify-center rounded-xl overflow-hidden shadow-glow-sm", iconDimensions)}>
        <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/20 via-blue-600/30 to-purple-600/30 blur-xs" />
        <img
          src="/zyntrix-mark.png"
          alt="Zyntrix AI"
          className="relative z-10 h-full w-full object-contain rounded-xl"
        />
      </div>

      {/* Brand Text */}
      {showText && (
        <div className="flex flex-col">
          <div className={cn("font-display font-bold tracking-tight text-white flex items-center gap-1.5 leading-none", textSizes, textClassName)}>
            <span>ZYNTRIX</span>
            <span className="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">AI</span>
          </div>
          {showTagline && (
            <span className="font-mono text-[9px] uppercase tracking-widest text-cyan-400/70 font-medium mt-1">
              Orchestrating Intelligence
            </span>
          )}
        </div>
      )}
    </div>
  );
}
