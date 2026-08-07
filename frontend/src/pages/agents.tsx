import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Plus,
  Trash2,
  Cpu,
  Zap,
  Play,
  X,
  Send,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Download,
  Search,
  SlidersHorizontal,
} from "lucide-react";

import { AgentForm } from "@/components/agent-form";
import { EmptyState } from "@/components/empty-state";
import { PageTransition } from "@/components/page-transition";
import { Tooltip } from "@/components/ui/tooltip";
import { useAgents, useCreateAgent, useDeleteAgent, useTestAgent } from "@/hooks/use-agents";
import type { Agent } from "@/types/agent";

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 16, scale: 0.96 },
  show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] } },
};

function AgentAvatar({ agent }: { agent: { name: string; avatar_color: string } }) {
  return (
    <div className="relative">
      <div
        className="flex h-12 w-12 items-center justify-center rounded-2xl text-base font-bold text-white shadow-lg transition-transform group-hover:scale-105"
        style={{
          backgroundColor: agent.avatar_color,
          boxShadow: `0 4px 16px ${agent.avatar_color}50`,
        }}
      >
        {agent.name.charAt(0).toUpperCase()}
      </div>
      <div className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-background bg-success shadow-sm" />
    </div>
  );
}

export function Agents() {
  const { data: agents = [], isLoading } = useAgents();
  const createAgent = useCreateAgent();
  const deleteAgent = useDeleteAgent();
  const testAgent = useTestAgent();

  const [showForm, setShowForm] = useState(false);
  const [testingAgent, setTestingAgent] = useState<Agent | null>(null);
  const [testPrompt, setTestPrompt] = useState("");
  const [testResponse, setTestResponse] = useState<string | null>(null);
  const [deletingAgent, setDeletingAgent] = useState<Agent | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [providerFilter, setProviderFilter] = useState<string>("all");

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleCloneAgent = (agent: Agent) => {
    createAgent.mutate(
      {
        name: `${agent.name} (Copy)`,
        description: agent.description ?? undefined,
        avatar_color: agent.avatar_color,
        instructions: agent.instructions ?? undefined,
        goal: agent.goal ?? undefined,
        personality: agent.personality ?? undefined,
        provider: agent.provider,
        model: agent.model,
        temperature: agent.temperature,
        max_tokens: agent.max_tokens,
      },
      {
        onSuccess: () => showToast(`Cloned "${agent.name}" successfully!`),
        onError: (err) => showToast(`Failed to clone agent: ${err}`),
      },
    );
  };

  const handleExportAgent = (agent: Agent) => {
    const jsonStr = JSON.stringify(agent, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `agent-${agent.name.toLowerCase().replace(/\s+/g, "-")}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Exported "${agent.name}" as JSON.`);
  };

  const handleDeleteConfirm = () => {
    if (!deletingAgent) return;
    const targetId = deletingAgent.id;
    deleteAgent.mutate(targetId, {
      onSuccess: () => {
        showToast("Agent deleted successfully.");
        setDeletingAgent(null);
      },
      onError: (err) => {
        showToast(`Failed to delete agent: ${err}`);
      },
    });
  };

  const handleRunTest = () => {
    if (!testPrompt.trim() || !testingAgent) return;
    setTestResponse(null);
    testAgent.mutate(
      { agentId: testingAgent.id, prompt: testPrompt.trim() },
      {
        onSuccess: (output) => setTestResponse(output),
        onError: (err) => setTestResponse(`Execution error: ${err}`),
      },
    );
  };

  // Filtered agents
  const providers = Array.from(new Set(agents.map((a) => a.provider)));
  const filteredAgents = agents.filter((agent) => {
    const matchesSearch =
      searchQuery === "" ||
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (agent.description && agent.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
      agent.model.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesProvider = providerFilter === "all" || agent.provider === providerFilter;
    return matchesSearch && matchesProvider;
  });

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-6 py-8 md:px-12">
        {/* Toast Notification */}
        <AnimatePresence>
          {toastMessage && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="fixed top-6 right-6 z-50 flex items-center gap-2 rounded-2xl border border-success/30 bg-surface/90 px-4 py-3 text-xs font-semibold text-success shadow-2xl backdrop-blur-xl"
            >
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{toastMessage}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Page Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="page-icon-wrap">
              <Bot className="h-5 w-5 text-accent" strokeWidth={1.75} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
                  Studio
                </span>
              </div>
              <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                AI Agents Studio
              </h1>
              <p className="text-sm text-white/40">
                Configure, test, clone, and deploy custom autonomous AI personas.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="font-mono text-[11px] text-white/30">
              {agents.length} persona{agents.length !== 1 ? "s" : ""}
            </span>
            <motion.button
              whileHover={{ scale: 1.03, y: -1 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 rounded-xl bg-gradient-brand px-4 py-2.5 text-xs font-bold text-white shadow-glow-sm transition-all"
            >
              <Plus className="h-4 w-4" strokeWidth={2} />
              Create Agent
            </motion.button>
          </div>
        </div>

        {/* Search & Filter Bar */}
        {agents.length > 0 && (
          <div className="mb-6 flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/30" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search agents by name, prompt, or model..."
                className="input pl-10 text-xs w-full"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            {providers.length > 1 && (
              <div className="flex items-center gap-2 w-full sm:w-auto shrink-0">
                <SlidersHorizontal className="h-3.5 w-3.5 text-white/30" />
                <select
                  value={providerFilter}
                  onChange={(e) => setProviderFilter(e.target.value)}
                  className="bg-surface/80 text-xs text-white border border-border/60 rounded-xl px-3 py-2 focus:outline-none cursor-pointer"
                >
                  <option value="all">All Providers</option>
                  {providers.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card h-52 skeleton rounded-2xl" />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && agents.length === 0 && (
          <EmptyState
            icon={Bot}
            title="No AI Agents Configured"
            description="Agents let you configure persistent system instructions, goals, and temperature settings for specialized AI personas."
            actionLabel="Create Agent"
            onAction={() => setShowForm(true)}
          />
        )}

        {/* Search Empty State */}
        {!isLoading && agents.length > 0 && filteredAgents.length === 0 && (
          <div className="glass-card border border-border/60 p-12 text-center my-8">
            <Search className="mx-auto h-8 w-8 text-white/20 mb-3" />
            <p className="text-sm font-semibold text-white">No agents match "{searchQuery}"</p>
            <button
              onClick={() => {
                setSearchQuery("");
                setProviderFilter("all");
              }}
              className="mt-3 text-xs text-accent underline"
            >
              Clear filters
            </button>
          </div>
        )}

        {/* Agent Cards Grid */}
        {!isLoading && filteredAgents.length > 0 && (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
          >
            {filteredAgents.map((agent) => (
              <motion.div
                key={agent.id}
                variants={cardVariants}
                whileHover={{ y: -4 }}
                className="glass-card group relative overflow-hidden flex flex-col border border-border/70 hover:border-primary/40 transition-all duration-300 rounded-2xl shadow-md"
              >
                {/* Top border glow */}
                <div
                  className="absolute top-0 left-0 right-0 h-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  style={{
                    background: `linear-gradient(90deg, transparent, ${agent.avatar_color}, transparent)`,
                  }}
                />

                <div className="relative z-10 p-5 flex-1 flex flex-col">
                  {/* Card Header: Avatar & Info */}
                  <div className="flex items-start gap-3.5 mb-3">
                    <AgentAvatar agent={agent} />
                    <div className="min-w-0 flex-1">
                      <h3 className="font-display text-base font-bold text-white truncate">
                        {agent.name}
                      </h3>
                      {agent.description ? (
                        <p className="mt-0.5 text-xs text-white/50 line-clamp-2 leading-relaxed">
                          {agent.description}
                        </p>
                      ) : (
                        <p className="mt-0.5 text-xs italic text-white/25">No description provided</p>
                      )}
                    </div>
                  </div>

                  {/* Instructions Snippet if available */}
                  {agent.instructions && (
                    <div className="mb-3 rounded-xl border border-white/5 bg-background/40 p-2.5 text-[11px] text-white/60 font-mono line-clamp-2">
                      <span className="text-accent/70 font-semibold block mb-0.5">Prompt:</span>
                      {agent.instructions}
                    </div>
                  )}

                  {/* Metadata Row */}
                  <div className="mt-auto pt-3 border-t border-border/40 flex items-center justify-between text-[11px]">
                    <div className="flex items-center gap-1.5 font-mono text-accent/90">
                      <Cpu className="h-3.5 w-3.5 text-accent/60" strokeWidth={1.75} />
                      <span>
                        {agent.provider}/{agent.model}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1 rounded-md bg-white/5 px-2 py-0.5 font-mono text-white/40">
                        <Zap className="h-3 w-3 text-warning/60" />
                        <span>{agent.temperature.toFixed(1)}</span>
                      </div>

                      <div className="flex items-center gap-1 rounded-full border border-success/30 bg-success/10 px-2 py-0.5 font-mono text-success">
                        <div className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
                        <span>Active</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card Action Bar: Run, Clone, Export, Delete */}
                <div className="relative z-10 border-t border-border/50 bg-surface/40 px-4 py-2.5 flex items-center justify-between gap-2">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => {
                      setTestingAgent(agent);
                      setTestPrompt("");
                      setTestResponse(null);
                    }}
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-gradient-brand px-3 py-2 text-xs font-bold text-white shadow-glow-sm transition-all"
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    Run Agent
                  </motion.button>

                  <Tooltip content="Clone Agent" side="top">
                    <button
                      onClick={() => handleCloneAgent(agent)}
                      className="flex h-8 w-8 items-center justify-center rounded-xl border border-border/60 bg-surface/60 text-white/40 hover:text-accent hover:border-accent/40 transition-all shrink-0"
                    >
                      <Copy className="h-3.5 w-3.5" />
                    </button>
                  </Tooltip>

                  <Tooltip content="Export JSON" side="top">
                    <button
                      onClick={() => handleExportAgent(agent)}
                      className="flex h-8 w-8 items-center justify-center rounded-xl border border-border/60 bg-surface/60 text-white/40 hover:text-white transition-all shrink-0"
                    >
                      <Download className="h-3.5 w-3.5" />
                    </button>
                  </Tooltip>

                  <Tooltip content="Delete agent" side="top">
                    <button
                      onClick={() => setDeletingAgent(agent)}
                      className="flex h-8 w-8 items-center justify-center rounded-xl border border-border/60 bg-surface/60 text-white/40 hover:text-danger hover:border-danger/40 hover:bg-danger/10 transition-all shrink-0"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </Tooltip>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* Run/Test Modal */}
        <AnimatePresence>
          {testingAgent && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="glass-card w-full max-w-xl p-6 border border-border/80 shadow-2xl rounded-2xl"
              >
                <div className="flex items-center justify-between pb-4 border-b border-border/50">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-9 w-9 items-center justify-center rounded-xl font-bold text-white text-sm"
                      style={{ backgroundColor: testingAgent.avatar_color }}
                    >
                      {testingAgent.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">Run Persona: {testingAgent.name}</h3>
                      <p className="text-[11px] text-white/40 font-mono">
                        {testingAgent.provider}/{testingAgent.model} · Temp {testingAgent.temperature}
                      </p>
                    </div>
                  </div>
                  <button onClick={() => setTestingAgent(null)} className="text-white/40 hover:text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div className="my-4 space-y-4">
                  {testingAgent.instructions && (
                    <div className="rounded-xl border border-border/60 bg-background/50 p-3 text-xs text-white/60">
                      <span className="font-mono text-[10px] uppercase text-accent font-semibold block mb-1">
                        System Instructions:
                      </span>
                      {testingAgent.instructions}
                    </div>
                  )}

                  <div>
                    <label className="text-xs text-white/40 mb-1.5 block font-medium">Test Prompt</label>
                    <div className="flex gap-2">
                      <input
                        value={testPrompt}
                        onChange={(e) => setTestPrompt(e.target.value)}
                        placeholder="Type prompt to execute against this agent..."
                        className="input flex-1 text-xs"
                        onKeyDown={(e) => e.key === "Enter" && handleRunTest()}
                        autoFocus
                      />
                      <button
                        onClick={handleRunTest}
                        disabled={testAgent.isPending || !testPrompt.trim()}
                        className="btn-primary text-xs px-4"
                      >
                        {testAgent.isPending ? (
                          <Sparkles className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Send className="h-3.5 w-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {testResponse && (
                    <div className="rounded-xl border border-primary/30 bg-primary/10 p-4 text-xs leading-relaxed text-white/90 max-h-64 overflow-y-auto font-mono">
                      <div className="font-mono text-[10px] text-accent mb-1.5 uppercase tracking-wider font-semibold">
                        Agent Output:
                      </div>
                      <div className="whitespace-pre-wrap">{testResponse}</div>
                    </div>
                  )}
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* Delete Confirmation Modal */}
        <AnimatePresence>
          {deletingAgent && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="glass-card w-full max-w-sm p-6 border border-border/80 shadow-2xl rounded-2xl"
              >
                <div className="flex items-center gap-3 text-danger mb-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-danger/10 border border-danger/30">
                    <AlertTriangle className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-display text-base font-bold text-white">Delete Agent?</h3>
                    <p className="text-xs text-white/40">This action cannot be undone.</p>
                  </div>
                </div>

                <p className="text-xs text-white/70 mb-6 leading-relaxed">
                  Are you sure you want to delete <span className="font-bold text-white">{deletingAgent.name}</span>?
                </p>

                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => setDeletingAgent(null)}
                    className="rounded-xl px-4 py-2 text-xs text-white/60 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDeleteConfirm}
                    disabled={deleteAgent.isPending}
                    className="rounded-xl bg-danger px-4 py-2 text-xs font-bold text-white shadow-glow-sm hover:bg-danger/90 transition-all disabled:opacity-50"
                  >
                    {deleteAgent.isPending ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* Create Agent Modal */}
        {showForm && <AgentForm onClose={() => setShowForm(false)} />}
      </div>
    </PageTransition>
  );
}
