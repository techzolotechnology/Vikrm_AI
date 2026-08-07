import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  Play,
  Wrench,
  XCircle,
  Terminal,
  Clock,
  Loader2,

  Search,
  ChevronRight,
  Cpu,
  Globe,
  Calculator,
  Code2,
  Database,
  Package,
} from "lucide-react";

import { PageTransition } from "@/components/page-transition";
import { Tooltip } from "@/components/ui/tooltip";
import { useExecuteTool, useToolExecutionHistory, useToolsList } from "@/hooks/use-tools";
import { cn } from "@/lib/utils";

// ─── Tool category detection ──────────────────────────────────────────────────

function getCategoryIcon(name: string) {
  const n = name.toLowerCase();
  if (n.includes("calc") || n.includes("math")) return { icon: Calculator, color: "#F59E0B", category: "Math" };
  if (n.includes("python") || n.includes("code") || n.includes("exec")) return { icon: Code2, color: "#7C3AED", category: "Code" };
  if (n.includes("web") || n.includes("search") || n.includes("http") || n.includes("fetch")) return { icon: Globe, color: "#22D3EE", category: "Web" };
  if (n.includes("db") || n.includes("data") || n.includes("sql")) return { icon: Database, color: "#22C55E", category: "Data" };
  if (n.includes("cpu") || n.includes("system") || n.includes("process")) return { icon: Cpu, color: "#EC4899", category: "System" };
  return { icon: Package, color: "#F97316", category: "General" };
}

export function Tools() {
  const { data: tools = [] } = useToolsList();
  const { data: history = [] } = useToolExecutionHistory();
  const executeTool = useExecuteTool();

  const [selectedTool, setSelectedTool] = useState<string>("");
  const [input, setInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const selectedToolDef = tools.find((t) => t.name === selectedTool);
  const { icon: ToolIcon, color: toolColor } = selectedToolDef
    ? getCategoryIcon(selectedToolDef.name)
    : { icon: Wrench, color: "#F97316" };

  const filteredTools = tools.filter(
    (t) =>
      searchQuery === "" ||
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description?.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  // Group by category
  const grouped = filteredTools.reduce<Record<string, typeof tools>>((acc, tool) => {
    const { category } = getCategoryIcon(tool.name);
    if (!acc[category]) acc[category] = [];
    acc[category].push(tool);
    return acc;
  }, {});

  const handleRun = () => {
    if (!input.trim() || !selectedTool) return;
    executeTool.mutate({ toolName: selectedTool, input: input.trim() });
  };

  // Set first tool as default when tools load
  if (!selectedTool && tools.length > 0) {
    setSelectedTool(tools[0].name);
  }

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        {/* Page Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className="page-icon-wrap"
              style={{
                background: "linear-gradient(135deg, rgba(249,115,22,0.2) 0%, rgba(234,88,12,0.1) 100%)",
                borderColor: "rgba(249,115,22,0.3)",
              }}
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
                Execute platform tools directly and inspect results in real-time.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 font-mono text-[11px] text-white/30">
            <div className="flex h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
            {tools.length} tools available
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
          {/* ─── Left: Tool Selector ─── */}
          <div className="space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/30" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tools..."
                className="input pl-9 text-xs w-full"
              />
            </div>

            {/* Tool List by Category */}
            <div className="glass-card border border-border/70 overflow-hidden">
              {Object.entries(grouped).length === 0 && (
                <p className="p-6 text-center text-xs text-white/30 font-mono">
                  No tools found.
                </p>
              )}
              {Object.entries(grouped).map(([category, categoryTools]) => {
                const { icon: CatIcon, color: catColor } = getCategoryIcon(categoryTools[0].name);
                return (
                  <div key={category}>
                    <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border/40 bg-surface/30">
                      <CatIcon className="h-3 w-3" style={{ color: catColor }} />
                      <span className="font-mono text-[10px] uppercase tracking-wider font-semibold" style={{ color: catColor }}>
                        {category}
                      </span>
                    </div>
                    {categoryTools.map((tool) => {
                      const { icon: TIcon, color } = getCategoryIcon(tool.name);
                      const isActive = selectedTool === tool.name;
                      return (
                        <motion.button
                          key={tool.name}
                          whileHover={{ x: 2 }}
                          onClick={() => setSelectedTool(tool.name)}
                          className={cn(
                            "flex w-full items-center gap-3 px-4 py-3 text-left transition-all border-b border-border/30 last:border-b-0",
                            isActive
                              ? "bg-orange-400/10 border-l-2 border-l-orange-400/60"
                              : "hover:bg-white/5",
                          )}
                        >
                          <div
                            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg"
                            style={{ backgroundColor: `${color}20`, border: `1px solid ${color}30` }}
                          >
                            <TIcon className="h-3.5 w-3.5" style={{ color }} strokeWidth={1.75} />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className={cn("font-mono text-xs font-semibold", isActive ? "text-orange-300" : "text-white/70")}>
                              {tool.name}
                            </p>
                            {tool.description && (
                              <p className="text-[10px] text-white/35 truncate mt-0.5">{tool.description}</p>
                            )}
                          </div>
                          {isActive && <ChevronRight className="h-3 w-3 text-orange-400/60 shrink-0" />}
                        </motion.button>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>

          {/* ─── Right: Execution Panel ─── */}
          <div className="space-y-4">
            {/* Tool Info + Execution */}
            <div className="glass-card border border-border/70 overflow-hidden shadow-2xl">
              {/* Tool Header */}
              {selectedToolDef ? (
                <div className="border-b border-border/50 bg-surface/20 p-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-10 w-10 items-center justify-center rounded-xl"
                      style={{ backgroundColor: `${toolColor}20`, border: `1px solid ${toolColor}30` }}
                    >
                      <ToolIcon className="h-5 w-5" style={{ color: toolColor }} strokeWidth={1.75} />
                    </div>
                    <div>
                      <p className="font-mono text-sm font-bold text-white">{selectedToolDef.name}</p>
                      <p className="text-xs text-white/45 mt-0.5">{selectedToolDef.description}</p>
                    </div>
                    <div className="ml-auto flex items-center gap-1.5">
                      <div className="h-1.5 w-1.5 rounded-full bg-success" />
                      <span className="font-mono text-[10px] text-white/30">Ready</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 text-center text-xs text-white/30">
                  Select a tool from the left panel
                </div>
              )}

              {/* Input */}
              <div className="p-4">
                <div className="flex gap-2 items-end">
                  <div className="flex-1 relative">
                    <Terminal className="pointer-events-none absolute left-3.5 top-3 h-3.5 w-3.5 text-white/25" />
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && e.ctrlKey) handleRun();
                      }}
                      placeholder={
                        selectedTool === "python_executor"
                          ? "print('Hello from Vikrm Python Sandbox')"
                          : selectedTool === "calculator"
                            ? "2 + 2 * 10"
                            : "Enter tool input parameters..."
                      }
                      rows={selectedTool === "python_executor" ? 5 : 3}
                      className="input resize-none text-sm pl-9 font-mono bg-background/60 w-full"
                    />
                  </div>
                  <Tooltip content="Execute (Ctrl+Enter)" side="top">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={handleRun}
                      disabled={executeTool.isPending || !input.trim() || !selectedTool}
                      className="flex shrink-0 items-center gap-2 rounded-xl bg-gradient-brand px-5 py-3 text-xs font-bold text-white shadow-glow-sm disabled:opacity-40 transition-all self-end"
                    >
                      {executeTool.isPending ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Play className="h-3.5 w-3.5" strokeWidth={2} />
                      )}
                      {executeTool.isPending ? "Running..." : "Execute"}
                    </motion.button>
                  </Tooltip>
                </div>
                <p className="mt-2 font-mono text-[10px] text-white/20">
                  Tip: Press <kbd className="rounded bg-white/10 px-1 py-0.5">Ctrl+Enter</kbd> to run
                </p>
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
                    <div
                      className={cn(
                        "p-4",
                        executeTool.data.status === "success" ? "bg-success/5" : "bg-danger/5",
                      )}
                    >
                      <div className="flex items-center gap-2 mb-3">
                        {executeTool.data.status === "success" ? (
                          <CheckCircle2 className="h-4 w-4 text-success" strokeWidth={1.75} />
                        ) : (
                          <XCircle className="h-4 w-4 text-danger" strokeWidth={1.75} />
                        )}
                        <span
                          className={cn(
                            "font-mono text-xs font-semibold",
                            executeTool.data.status === "success" ? "text-success/80" : "text-danger/80",
                          )}
                        >
                          {executeTool.data.status === "success" ? "Success" : "Error"}
                        </span>
                        <span className="font-mono text-[10px] text-white/30">
                          · {executeTool.data.duration_ms}ms
                        </span>
                      </div>
                      <pre className="text-xs font-mono text-white/85 whitespace-pre-wrap leading-relaxed bg-background/60 rounded-xl p-4 border border-border/40 max-h-64 overflow-y-auto">
                        {executeTool.data.output_text ?? executeTool.data.error}
                      </pre>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* ─── Execution History ─── */}
            <div>
              <div className="mb-3 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-white/30" strokeWidth={1.75} />
                <h2 className="font-display text-sm font-semibold text-white/60">Execution History</h2>
                {history.length > 0 && (
                  <span className="ml-auto font-mono text-[10px] text-white/25">
                    {history.length} runs
                  </span>
                )}
              </div>

              {history.length === 0 ? (
                <div className="glass-card border border-border/50 p-8 text-center">
                  <Terminal className="mx-auto h-8 w-8 text-white/10 mb-3" strokeWidth={1} />
                  <p className="text-xs text-white/30">No execution logs yet. Run a tool above.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((execution, index) => (
                    <motion.div
                      key={execution.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.02 }}
                      className="glass-card flex items-center justify-between gap-3 p-3.5 border border-border/70 hover:border-white/10 transition-all"
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <div
                          className={cn(
                            "flex h-6 w-6 shrink-0 items-center justify-center rounded-full",
                            execution.status === "success"
                              ? "bg-success/15 border border-success/25"
                              : "bg-danger/15 border border-danger/25",
                          )}
                        >
                          {execution.status === "success" ? (
                            <CheckCircle2 className="h-3 w-3 text-success" />
                          ) : (
                            <XCircle className="h-3 w-3 text-danger" />
                          )}
                        </div>
                        <div
                          className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md"
                          style={{
                            backgroundColor: `${getCategoryIcon(execution.tool_name).color}20`,
                            border: `1px solid ${getCategoryIcon(execution.tool_name).color}30`,
                          }}
                        >
                          {(() => {
                            const { icon: HIcon, color } = getCategoryIcon(execution.tool_name);
                            return <HIcon className="h-3 w-3" style={{ color }} />;
                          })()}
                        </div>
                        <span className="shrink-0 font-mono text-xs font-bold text-orange-300/80">
                          {execution.tool_name}
                        </span>
                        <span className="truncate font-mono text-xs text-white/35">
                          {execution.input_text}
                        </span>
                      </div>
                      <div className="flex shrink-0 items-center gap-2 text-white/30">
                        <Clock className="h-3 w-3" strokeWidth={1.75} />
                        <span className="font-mono text-[10px]">{execution.duration_ms}ms</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
