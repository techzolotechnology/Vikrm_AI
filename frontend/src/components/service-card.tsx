import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type ServiceStatus = "up" | "down" | "checking";

interface ServiceCardProps {
  index: number;
  icon: LucideIcon;
  name: string;
  description: string;
  status: ServiceStatus | string;
}

const STATUS_CONFIG = {
  up: {
    label: "Operational",
    color: "#22C55E",
    bg: "bg-success/15",
    border: "border-success/30",
    text: "text-success",
    dotClass: "bg-success",
    glow: "rgba(34, 197, 94, 0.3)",
  },
  down: {
    label: "Unavailable",
    color: "#EF4444",
    bg: "bg-danger/15",
    border: "border-danger/30",
    text: "text-danger",
    dotClass: "bg-danger",
    glow: "rgba(239, 68, 68, 0.3)",
  },
  checking: {
    label: "Checking...",
    color: "#F59E0B",
    bg: "bg-warning/15",
    border: "border-warning/30",
    text: "text-warning",
    dotClass: "bg-warning",
    glow: "rgba(245, 158, 11, 0.3)",
  },
};

export function ServiceCard({ index, icon: Icon, name, description, status }: ServiceCardProps) {
  const cfg = STATUS_CONFIG[status as ServiceStatus] ?? STATUS_CONFIG.checking;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 + 0.3, duration: 0.4 }}
      whileHover={{ y: -3 }}
      className="glass-card group relative overflow-hidden p-5 border border-border/80 hover:border-primary/20 transition-all duration-300"
    >
      {/* Background glow on hover */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl"
        style={{
          background: `radial-gradient(ellipse at 50% 0%, ${cfg.glow} 0%, transparent 65%)`,
        }}
      />

      {/* Top shimmer */}
      <div
        className="absolute top-0 left-0 right-0 h-px"
        style={{
          background: `linear-gradient(90deg, transparent, ${cfg.color}50, transparent)`,
        }}
      />

      <div className="relative z-10">
        <div className="flex items-start justify-between">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl"
            style={{
              background: `${cfg.color}15`,
              border: `1px solid ${cfg.color}30`,
            }}
          >
            <Icon className="h-5 w-5" style={{ color: cfg.color }} strokeWidth={1.75} />
          </div>

          {/* Status pill */}
          <div
            className={cn(
              "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold font-mono",
              cfg.bg,
              cfg.border,
              cfg.text,
            )}
          >
            <div className="relative flex h-1.5 w-1.5">
              {status === "up" && (
                <div
                  className="absolute h-full w-full animate-ping rounded-full opacity-75"
                  style={{ backgroundColor: cfg.color }}
                />
              )}
              <div
                className="relative h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: cfg.color }}
              />
            </div>
            {cfg.label}
          </div>
        </div>

        <h3 className="mt-3 font-display text-sm font-bold text-white group-hover:text-white transition-colors">
          {name}
        </h3>
        <p className="mt-1 font-mono text-[11px] text-white/40 leading-relaxed">
          {description}
        </p>
      </div>
    </motion.div>
  );
}
