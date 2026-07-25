import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Play, Wrench, XCircle, Terminal, Clock, Loader2, Zap } from "lucide-react";

import { PageTransition } from "@/components/page-transition";
import { useExecuteTool, useToolExecutionHistory, useToolsList } from "@/hooks/use-tools";
import { cn } from "@/lib/utils";

export function Tools() {
  const { data: tools = [] } = useToolsList();
  const { data: history = [] } = useToolExecutionHistory();
  const executeTool = useExecuteTool();

  const [selectedTool, setSelectedTool] = useState<string>("calculator");
  const [input, setInput] = useState("");

  const handleRun = () => {
    if (!input.trim()) return;
    executeTool.mutate({ toolName: selectedTool, input: input.trim() });
  };

  const selectedToolDef = tools.find((t) => t.name === selectedTool);

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        <div className="mx-auto max-w-4xl">
          {/* Page Header */}
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div
                className="page-icon-wrap"
                style={{ background: "linear-gradient(135deg, rgba(249,115,22,0.2) 0%, rgba(234,88,12,0.1) 100%)", borderColor: "rgba(249,115,22,0.3)" }}
              >
                <Wrench className="h-5 w-5" style={{ color: "#F97316" }} strokeWidth={1.75} />
              </div>
              <div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
                  Testing Console
                </span>
                <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                  System Tools
                </h1>
                <p className="text-sm text-white/40">
                  Execute registered platform tools directly outside of workflows.
                </p>
              </div>
            </div>
          </div>

          {/* Tool Selector + Execution Panel */}
          <div className="mb-6 glass-card border border-border/70 overflow-hidden shadow-2xl">
            {/* Tool tabs */}
            <div className="border-b border-border/50 p-4">
              <p className="mb-3 font-mono text-[10px] uppercase tracking-wider text-white/30">Available Tools</p>
              <div className="flex flex-wrap gap-2">
                {tools.map((tool) => (
                  <motion.button
                    key={tool.name}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={() => setSelectedTool(tool.name)}
                    className={cn(
                      "flex items-center gap-1.5 rounded-xl border px-3.5 py-2 font-mono text-xs font-semibold transition-all duration-200",
                      selectedTool === tool.name
                        ? "border-orange-400/40 bg-orange-400/15 text-orange-300 shadow-sm"
                        : "border-border/70 bg-surface/40 text-white/50 hover:text-white hover:border-white/20",
                    )}
                  >
                    <Wrench className="h-3 w-3" strokeWidth={1.75} />
                    {tool.name}
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Tool description */}
            {selectedToolDef && (
              <div className="border-b border-border/40 px-4 py-3 bg-surface/20">
                <div className="flex items-center gap-2">
                  <Zap className="h-3.5 w-3.5 text-orange-400/60" strokeWidth={1.75} />
                  <p className="text-xs font-mono text-white/50 leading-relaxed">
                    {selectedToolDef.description}
                  </p>
                </div>
              </div>
            )}

            {/* Input area */}
            <div className="p-4">
              <div className="flex gap-2 items-end">
                <div className="flex-1 relative">
                  <Terminal className="pointer-events-none absolute left-3.5 top-3 h-3.5 w-3.5 text-white/25" />
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={
                      selectedTool === "python_executor"
                        ? "print('Hello from Vikrm Python Sandbox')"
                        : "Enter tool input parameters..."
                    }
                    rows={selectedTool === "python_executor" ? 4 : 2}
                    className="input resize-none text-sm pl-9 font-mono bg-background/60"
                  />
                </div>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleRun}
                  disabled={executeTool.isPending || !input.trim()}
                  className="flex shrink-0 items-center gap-2 rounded-xl bg-gradient-brand px-5 py-2.5 text-xs font-bold text-white shadow-glow-sm disabled:opacity-40 transition-all self-end"
                >
                  {executeTool.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Play className="h-3.5 w-3.5" strokeWidth={2} />
                  )}
                  {executeTool.isPending ? "Running..." : "Execute"}
                </motion.button>
              </div>
            </div>

            {/* Output */}
            <AnimatePresence>
              {executeTool.data && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="border-t border-border/40"
                >
                  <div className={cn(
                    "p-4",
                    executeTool.data.status === "success"
                      ? "bg-success/5"
                      : "bg-danger/5",
                  )}>
                    <div className="flex items-center gap-2 mb-2">
                      {executeTool.data.status === "success" ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-success" strokeWidth={1.75} />
                      ) : (
                        <XCircle className="h-3.5 w-3.5 text-danger" strokeWidth={1.75} />
                      )}
                      <span className={cn(
                        "font-mono text-[11px] font-semibold",
                        executeTool.data.status === "success" ? "text-success/80" : "text-danger/80",
                      )}>
                        {executeTool.data.status === "success" ? "Success" : "Error"} · {executeTool.data.duration_ms}ms
                      </span>
                    </div>
                    <pre className="text-xs font-mono text-white/85 whitespace-pre-wrap leading-relaxed bg-background/60 rounded-xl p-3 border border-border/40">
                      {executeTool.data.output_text ?? executeTool.data.error}
                    </pre>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Execution History */}
          <div className="mb-4 flex items-center gap-2">
            <Terminal className="h-4 w-4 text-white/30" strokeWidth={1.75} />
            <h2 className="font-display text-sm font-semibold text-white/60">Execution History</h2>
            {history.length > 0 && (
              <span className="ml-auto font-mono text-[10px] text-white/25">{history.length} runs</span>
            )}
          </div>

          <div className="space-y-2">
            {history.length === 0 && (
              <p className="py-8 text-center text-xs text-white/25 font-mono">
                No execution logs recorded yet.
              </p>
            )}
            {history.map((execution, index) => (
              <motion.div
                key={execution.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.02 }}
                className="glass-card flex items-center justify-between gap-3 p-3.5 border border-border/70 hover:border-white/10 transition-all"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className={cn(
                    "flex h-6 w-6 shrink-0 items-center justify-center rounded-full",
                    execution.status === "success"
                      ? "bg-success/15 border border-success/25"
                      : "bg-danger/15 border border-danger/25",
                  )}>
                    {execution.status === "success" ? (
                      <CheckCircle2 className="h-3 w-3 text-success" />
                    ) : (
                      <XCircle className="h-3 w-3 text-danger" />
                    )}
                  </div>
                  <span className="shrink-0 font-mono text-xs font-bold text-orange-300/80">
                    {execution.tool_name}
                  </span>
                  <span className="truncate font-mono text-xs text-white/40">{execution.input_text}</span>
                </div>
                <div className="flex shrink-0 items-center gap-2 text-white/30">
                  <Clock className="h-3 w-3" strokeWidth={1.75} />
                  <span className="font-mono text-[10px]">{execution.duration_ms}ms</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
