import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, ChevronDown, Play, Sparkles, XCircle, Clock } from "lucide-react";

import { cn } from "@/lib/utils";
import type { WorkflowRun } from "@/types/workflow";

interface RunPanelProps {
  onRun: (input: string) => void;
  isRunning: boolean;
  latestRun: WorkflowRun | undefined;
}

export function RunPanel({ onRun, isRunning, latestRun }: RunPanelProps) {
  const [input, setInput] = useState("");
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  const handleRun = () => {
    onRun(input);
  };

  return (
    <div className="glass-card-elevated absolute bottom-4 left-4 right-4 z-20 mx-auto max-w-3xl p-4 shadow-2xl backdrop-blur-2xl border border-border/80 rounded-2xl">
      {/* Input bar */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRun()}
            placeholder="Execute workflow with input (e.g. 'Generate project summary')..."
            className="input pl-9 pr-12 text-xs bg-background/60 border-border/80"
          />
          <Sparkles className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-accent" />
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 font-mono text-[10px] text-white/30">
            ↵ Enter
          </span>
        </div>

        <motion.button
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.96 }}
          onClick={handleRun}
          disabled={isRunning}
          className="flex shrink-0 items-center gap-1.5 rounded-xl bg-gradient-brand px-5 py-2.5 text-xs font-bold text-white shadow-glow-sm disabled:opacity-40"
        >
          <Play className="h-3.5 w-3.5" strokeWidth={2} />
          {isRunning ? "Executing..." : "Run"}
        </motion.button>
      </div>

      {/* Execution Telemetry Log */}
      {latestRun && (
        <div className="mt-3.5 max-h-60 space-y-1.5 overflow-y-auto no-scrollbar border-t border-border/50 pt-3">
          <div className="flex items-center justify-between text-xs font-semibold">
            <div className="flex items-center gap-2">
              {latestRun.status === "completed" ? (
                <CheckCircle2 className="h-4 w-4 text-success" />
              ) : (
                <XCircle className="h-4 w-4 text-danger" />
              )}
              <span className="text-white">
                Workflow {latestRun.status === "completed" ? "Completed" : "Failed"}
              </span>
              <span className="rounded-full bg-white/10 px-2 py-0.2 font-mono text-[10px] text-white/50">
                {latestRun.steps.length} step{latestRun.steps.length !== 1 ? "s" : ""}
              </span>
            </div>
            <span className="font-mono text-[10px] text-white/30 flex items-center gap-1">
              <Clock className="h-3 w-3" /> Telemetry Log
            </span>
          </div>

          <div className="space-y-1.5 pt-1">
            {latestRun.steps.map((step) => {
              const isExpanded = expandedStep === step.node_id;
              return (
                <div
                  key={step.node_id}
                  className="rounded-xl border border-border/60 bg-surface/50 overflow-hidden transition-all"
                >
                  <button
                    onClick={() => setExpandedStep(isExpanded ? null : step.node_id)}
                    className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left hover:bg-white/5 transition"
                  >
                    <div className="flex items-center gap-2 text-xs">
                      {step.status === "success" ? (
                        <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" />
                      ) : (
                        <XCircle className="h-3.5 w-3.5 shrink-0 text-danger" />
                      )}
                      <span className="font-mono font-bold text-accent">{step.node_id}</span>
                      <span className="rounded bg-white/5 px-1.5 py-0.2 font-mono text-[10px] text-white/40">
                        {step.node_type}
                      </span>
                    </div>
                    <ChevronDown
                      className={cn(
                        "h-3.5 w-3.5 text-white/30 transition-transform",
                        isExpanded && "rotate-180 text-white",
                      )}
                    />
                  </button>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="space-y-1 px-3.5 pb-3 font-mono text-[11px] text-white/70 border-t border-border/40 pt-2"
                      >
                        <p>
                          <span className="text-white/30">input:</span> {step.input_summary}
                        </p>
                        <p>
                          <span className="text-white/30">output:</span> {step.output || "—"}
                        </p>
                        {step.error && <p className="text-danger">error: {step.error}</p>}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>

          {latestRun.final_output && (
            <div className="mt-2.5 rounded-xl border border-primary/30 bg-primary/10 p-3 text-xs text-white/90 shadow-glow-sm">
              <span className="text-[10px] font-bold uppercase tracking-wider text-accent block mb-1">
                Final Workflow Output
              </span>
              <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed">
                {latestRun.final_output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
