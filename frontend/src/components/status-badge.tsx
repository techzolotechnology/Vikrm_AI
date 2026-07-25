import { cn } from "@/lib/utils";

type Status = "up" | "down" | "ready" | "degraded" | "checking";

const STATUS_STYLES: Record<Status, string> = {
  up: "bg-success/10 text-success border-success/30",
  ready: "bg-success/10 text-success border-success/30",
  down: "bg-danger/10 text-danger border-danger/30",
  degraded: "bg-warning/10 text-warning border-warning/30",
  checking: "bg-white/5 text-white/50 border-white/10",
};

const STATUS_LABEL: Record<Status, string> = {
  up: "Operational",
  ready: "Operational",
  down: "Unreachable",
  degraded: "Degraded",
  checking: "Checking",
};

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-mono font-medium",
        STATUS_STYLES[status],
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          status === "up" || status === "ready"
            ? "bg-success"
            : status === "down"
              ? "bg-danger"
              : status === "degraded"
                ? "bg-warning"
                : "bg-white/40",
        )}
      />
      {STATUS_LABEL[status]}
    </span>
  );
}
