import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  index: number;
  icon: LucideIcon;
  label: string;
  value: number | string;
  subtext?: string;
  color?: string;
}

function useCountUp(target: number, duration = 1200) {
  const [count, setCount] = useState(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (typeof target !== "number" || isNaN(target)) return;
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(eased * target));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return count;
}

export function StatCard({ index, icon: Icon, label, value, subtext, color = "#7C3AED" }: StatCardProps) {
  const numericValue = typeof value === "number" ? value : parseInt(String(value), 10);
  const isNumeric = !isNaN(numericValue) && typeof value === "number";
  const displayCount = useCountUp(isNumeric ? numericValue : 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.06, duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
      whileHover={{ y: -4, scale: 1.02 }}
      className="stat-card group relative overflow-hidden cursor-default"
    >
      {/* Background glow */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl"
        style={{
          background: `radial-gradient(ellipse at 30% 30%, ${color}18 0%, transparent 70%)`,
        }}
      />

      {/* Top shimmer line */}
      <div
        className="absolute top-0 left-0 right-0 h-px opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: `linear-gradient(90deg, transparent, ${color}60, transparent)`,
        }}
      />

      <div className="relative z-10">
        {/* Icon */}
        <div
          className="flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-300 group-hover:scale-110"
          style={{
            background: `${color}18`,
            border: `1px solid ${color}30`,
            boxShadow: `0 0 12px ${color}20`,
          }}
        >
          <Icon className="h-4 w-4" style={{ color }} strokeWidth={1.75} />
        </div>

        {/* Value */}
        <motion.p
          className="mt-3 font-display text-2xl font-bold tracking-tight text-white"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: index * 0.06 + 0.2 }}
        >
          {isNumeric ? displayCount.toLocaleString() : (value === "—" ? "—" : value)}
        </motion.p>

        {/* Label */}
        <p className="mt-0.5 text-[11px] font-medium text-white/50">{label}</p>

        {/* Subtext */}
        {subtext && (
          <p className="mt-1 font-mono text-[10px] text-white/30">{subtext}</p>
        )}
      </div>
    </motion.div>
  );
}
