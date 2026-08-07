import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Play,
  Sparkles,
  XCircle,
  Clock,
  Loader2,
  X,
  Terminal,
  Zap,
  AlertCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { WorkflowRun } from "@/types/workflow";

interface RunPanelProps {
  onRun: (input: string) => void;
  isRunning: boolean;
  latestRun: WorkflowRun | undefined;
  onClose?: () => void;
}

export function RunPanel({ onRun, isRunning, latestRun, onClose }: RunPanelProps) {
  const [input, setInput] = useState("");
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  const handleRun = () => {
    if (!input.trim()) return;
    onRun(input);
  };

  const statusBg = latestRun?.status === "completed"
    ? "border-success/30 bg-success/5"
    : latestRun?.status === "failed"
      ? "border-danger/30 bg-danger/5"
      : "border-border/60 bg-surface/50";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.98 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className="absolute bottom-16 left-4 right-4 z-20 mx-auto max-w-2xl"
    >
      <div className="glass-card border border-border/80 shadow-2xl backdrop-blur-2xl overflow-hidden">
        {/* Panel Header */}
        <div className="flex items-center justify-between border-b border-border/50 bg-surface/40 px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary/20 border border-primary/30">
              <Terminal className="h-3.5 w-3.5 text-accent" />
            </div>
            <span className="font-display text-xs font-bold text-white">Execution Console</span>
            {isRunning && (
              <motion.div
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 1.2, repeat: Infinity }}
                className="flex items-center gap-1 rounded-full bg-accent/15 border border-accent/20 px-2 py-0.5"
              >
                <div className="h-1.5 w-1.5 rounded-full bg-accent" />
                <span className="font-mono text-[9px] text-accent">Running</span>
              </motion.div>
            )}
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-white/40 hover:text-white transition-colors"
              aria-label="Close run panel"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Input bar */}
        <div className="p-3 border-b border-border/40">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Sparkles className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-accent/60" />
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleRun()}
                placeholder="Enter workflow input (e.g. 'Generate a project summary')"
                className="input pl-9 pr-14 text-xs bg-background/50 border-border/70"
                aria-label="Workflow input"
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 font-mono text-[10px] text-white/25">
                ↵
              </span>
            </div>
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={handleRun}
              disabled={isRunning || !input.trim()}
              className="flex shrink-0 items-center gap-1.5 rounded-xl bg-gradient-brand px-4 py-2 text-xs font-bold text-white shadow-glow-sm disabled:opacity-40 transition-all"
              aria-label="Run workflow"
            >
              {isRunning ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Play className="h-3.5 w-3.5" strokeWidth={2} />
              )}
              {isRunning ? "Running..." : "Execute"}
            </motion.button>
          </div>
        </div>

        {/* Results */}
        <AnimatePresence>
          {latestRun && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="max-h-72 overflow-y-auto no-scrollbar p-3 space-y-2">
                {/* Status header */}
                <div className={cn("flex items-center justify-between rounded-xl border px-3 py-2", statusBg)}>
                  <div className="flex items-center gap-2 text-xs font-semibold">
                    {latestRun.status === "completed" ? (
                      <CheckCircle2 className="h-4 w-4 text-success" />
                    ) : latestRun.status === "failed" ? (
                      <XCircle className="h-4 w-4 text-danger" />
                    ) : (
                      <Loader2 className="h-4 w-4 text-accent animate-spin" />
                    )}
                    <span className="text-white">
                      {latestRun.status === "completed"
                        ? "Workflow Completed Successfully"
                        : latestRun.status === "failed"
                          ? "Workflow Failed"
                          : "Executing..."}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-white/10 px-2 py-0.5 font-mono text-[10px] text-white/50">
                      {latestRun.steps.length} steps
                    </span>
                    <span className="font-mono text-[10px] text-white/30 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(latestRun.started_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>

                {/* Step Results */}
                {latestRun.steps.map((step, i) => {
                  const isExpanded = expandedStep === step.node_id;
                  return (
                    <motion.div
                      key={step.node_id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="rounded-xl border border-border/60 bg-surface/40 overflow-hidden"
                    >
                      <button
                        onClick={() => setExpandedStep(isExpanded ? null : step.node_id)}
                        className="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-left hover:bg-white/5 transition"
                        aria-expanded={isExpanded}
                      >
                        <div className="flex items-center gap-2.5 text-xs">
                          {step.status === "success" ? (
                            <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" />
                          ) : step.status === "failed" ? (
                            <XCircle className="h-3.5 w-3.5 shrink-0 text-danger" />
                          ) : (
                            <Loader2 className="h-3.5 w-3.5 shrink-0 text-accent animate-spin" />
                          )}
                          <span className="font-mono font-bold text-accent">{step.node_id}</span>
                          <span className="rounded bg-white/8 px-1.5 py-0.5 font-mono text-[9px] text-white/40 uppercase tracking-wider">
                            {step.node_type}
                          </span>
                          {step.status === "failed" && (
                            <AlertCircle className="h-3 w-3 text-danger" />
                          )}
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="h-3.5 w-3.5 text-white/30 shrink-0" />
                        ) : (
                          <ChevronDown className="h-3.5 w-3.5 text-white/30 shrink-0" />
                        )}
                      </button>

                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="space-y-1.5 px-3.5 pb-3 font-mono text-[11px] text-white/70 border-t border-border/40 pt-2.5"
                          >
                            <p>
                              <span className="text-white/30 mr-2">input:</span>
                              <span>{step.input_summary}</span>
                            </p>
                            <p>
                              <span className="text-white/30 mr-2">output:</span>
                              <span className={step.status === "failed" ? "text-danger/80" : ""}>
                                {step.output || step.error || "—"}
                              </span>
                            </p>
                            {step.error && (
                              <p className="text-danger flex items-center gap-1.5">
                                <AlertCircle className="h-3 w-3" />
                                {step.error}
                              </p>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  );
                })}

                {/* Final output */}
                {latestRun.final_output && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="rounded-xl border border-primary/30 bg-primary/8 p-4 shadow-glow-sm"
                  >
                    <div className="mb-2 flex items-center gap-1.5">
                      <Zap className="h-3.5 w-3.5 text-accent" />
                      <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-accent">
                        Workflow Output
                      </span>
                    </div>
                    <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-white/90">
                      {latestRun.final_output}
                    </pre>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
