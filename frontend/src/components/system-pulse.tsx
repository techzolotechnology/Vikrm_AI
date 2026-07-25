import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Cpu } from "lucide-react";

interface SystemPulseProps {
  isReady: boolean;
  isLoading: boolean;
}

export function SystemPulse({ isReady, isLoading }: SystemPulseProps) {
  const [timeStr, setTimeStr] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    };
    updateTime();
    const interval = setInterval(updateTime, 10000);
    return () => clearInterval(interval);
  }, []);

  const status = isLoading ? "checking" : isReady ? "operational" : "degraded";

  return (
    <div className="flex items-center gap-3">
      {/* Live status pill */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="hidden sm:flex items-center gap-2 rounded-xl border border-border/60 bg-surface/50 px-3.5 py-2 backdrop-blur-sm"
      >
        <div className="relative flex h-2 w-2">
          <div className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-60 ${
            status === "operational" ? "bg-success" : status === "degraded" ? "bg-danger" : "bg-warning"
          }`} />
          <div className={`relative inline-flex h-2 w-2 rounded-full ${
            status === "operational" ? "bg-success" : status === "degraded" ? "bg-danger" : "bg-warning"
          }`} />
        </div>
        <span className="font-mono text-xs text-white/50">
          {isLoading ? "Checking..." : isReady ? "System Online" : "Degraded"}
        </span>
      </motion.div>

      {/* Clock */}
      <div className="hidden lg:flex items-center gap-1.5 rounded-xl border border-border/40 bg-surface/30 px-3 py-2">
        <Cpu className="h-3 w-3 text-accent/50" strokeWidth={1.75} />
        <span className="font-mono text-xs text-white/35">{timeStr}</span>
      </div>

      {/* Activity icon */}
      <div className="flex items-center gap-1.5 rounded-xl border border-border/40 bg-surface/30 px-3 py-2">
        <Activity className={`h-3.5 w-3.5 ${status === "operational" ? "text-success/60" : "text-warning/60"}`} strokeWidth={1.75} />
      </div>
    </div>
  );
}
