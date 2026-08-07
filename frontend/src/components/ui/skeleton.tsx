import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  variant?: "line" | "circle" | "rect";
  width?: string | number;
  height?: string | number;
  lines?: number;
}

export function Skeleton({ className, variant = "rect", width, height, lines = 1 }: SkeletonProps) {
  const base = "skeleton rounded-xl";

  if (variant === "circle") {
    return (
      <div
        className={cn(base, "rounded-full", className)}
        style={{ width: width ?? 40, height: height ?? 40 }}
      />
    );
  }

  if (variant === "line") {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(base, "h-3", className)}
            style={{ width: i === lines - 1 && lines > 1 ? "70%" : "100%" }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(base, className)}
      style={{ width, height }}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="glass-card border border-border/60 p-5 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton variant="circle" width={40} height={40} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="line" />
          <Skeleton className="h-2 w-2/3" variant="rect" />
        </div>
      </div>
      <Skeleton className="h-16" />
    </div>
  );
}

export function StatSkeleton() {
  return (
    <div className="glass-card border border-border/60 p-4 space-y-2">
      <Skeleton className="h-2 w-16" />
      <Skeleton className="h-8 w-24" />
      <Skeleton className="h-2 w-20" />
    </div>
  );
}
