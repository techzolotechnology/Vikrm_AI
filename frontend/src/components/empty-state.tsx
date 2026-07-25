import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ icon: Icon, title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
      className="flex flex-col items-center justify-center py-20 px-6 text-center"
    >
      {/* Animated icon container */}
      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 3, ease: "easeInOut", repeat: Infinity }}
        className="relative"
      >
        {/* Outer glow ring */}
        <div className="absolute inset-0 rounded-full bg-primary/10 blur-xl scale-150" />
        {/* Icon box */}
        <div className="relative flex h-20 w-20 items-center justify-center rounded-3xl border border-primary/20 bg-primary/10 backdrop-blur-sm">
          <Icon className="h-9 w-9 text-primary/60" strokeWidth={1.5} />
        </div>
      </motion.div>

      {/* Decorative dots */}
      <div className="mt-6 flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            animate={{ opacity: [0.2, 0.8, 0.2] }}
            transition={{ duration: 2, delay: i * 0.3, repeat: Infinity }}
            className="h-1 w-1 rounded-full bg-primary/40"
          />
        ))}
      </div>

      <h3 className="mt-4 font-display text-base font-bold text-white/80">{title}</h3>

      {description && (
        <p className="mt-2 max-w-sm text-xs leading-relaxed text-white/40">{description}</p>
      )}

      {actionLabel && onAction && (
        <motion.button
          whileHover={{ scale: 1.04, y: -1 }}
          whileTap={{ scale: 0.97 }}
          onClick={onAction}
          className="mt-6 flex items-center gap-2 rounded-xl bg-gradient-brand px-5 py-2.5 text-xs font-bold text-white shadow-glow-sm transition-all"
        >
          {actionLabel}
        </motion.button>
      )}
    </motion.div>
  );
}
