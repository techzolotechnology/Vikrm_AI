import type { ElementType } from "react";
import { motion } from "framer-motion";
import {
  Bot,
  CheckCircle2,
  Circle,
  FileText,
  MessageSquare,
  Users,
  Workflow,
  XCircle,
} from "lucide-react";

import type { ActivityItem } from "@/types/analytics";

const TYPE_ICON: Record<ActivityItem["type"], ElementType> = {
  conversation: MessageSquare,
  workflow_run: Workflow,
  team_run: Users,
  tool_execution: Bot,
  document: FileText,
};

const TYPE_COLOR: Record<ActivityItem["type"], string> = {
  conversation: "bg-purple-500/15 border-purple-500/30 text-purple-400",
  workflow_run: "bg-amber-500/15 border-amber-500/30 text-amber-400",
  team_run: "bg-pink-500/15 border-pink-500/30 text-pink-400",
  tool_execution: "bg-cyan-500/15 border-cyan-500/30 text-cyan-400",
  document: "bg-emerald-500/15 border-emerald-500/30 text-emerald-400",
};

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function ActivityFeed({ items }: { items: ActivityItem[] }) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-10 text-center">
        <Circle className="h-8 w-8 text-white/15" strokeWidth={1} />
        <p className="text-xs text-white/30">Activity stream is quiet.</p>
        <p className="text-[11px] text-white/20">Events will appear here as you use Vikrm.</p>
      </div>
    );
  }

  return (
    <div className="relative space-y-1">
      {/* Timeline line */}
      <div className="absolute left-[17px] top-4 bottom-4 w-px bg-gradient-to-b from-primary/20 via-white/10 to-transparent" />

      {items.map((item, index) => {
        const Icon = TYPE_ICON[item.type];
        const colorClass = TYPE_COLOR[item.type];
        const isSuccess =
          item.status === "completed" || item.status === "success" || item.status === "ready";
        const isFailed = item.status === "failed";

        return (
          <motion.div
            key={`${item.type}-${item.title}-${item.timestamp}-${index}`}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.03, duration: 0.25 }}
            className="relative flex items-start gap-3.5 rounded-xl px-3 py-2.5 hover:bg-white/[0.03] transition group"
          >
            <div
              className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${colorClass}`}
            >
              <Icon className="h-3.5 w-3.5" strokeWidth={1.75} />
            </div>

            <div className="flex min-w-0 flex-1 items-center justify-between gap-3">
              <span className="min-w-0 flex-1 truncate text-xs font-medium text-white/75 group-hover:text-white/90 transition-colors">
                {item.title}
              </span>
              <div className="flex shrink-0 items-center gap-2">
                {item.status && (
                  <span className="shrink-0">
                    {isSuccess ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-success" strokeWidth={1.75} />
                    ) : isFailed ? (
                      <XCircle className="h-3.5 w-3.5 text-danger" strokeWidth={1.75} />
                    ) : (
                      <span className="rounded-full bg-warning/20 px-1.5 py-0.5 font-mono text-[9px] text-warning">
                        {item.status}
                      </span>
                    )}
                  </span>
                )}
                <span className="font-mono text-[10px] text-white/25">{timeAgo(item.timestamp)}</span>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
