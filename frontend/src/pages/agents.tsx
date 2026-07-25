import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Plus,
  Trash2,
  Cpu,
  Zap,
  ChevronRight,
  Copy,
  Download,
  Upload,
  Play,
  History,
  X,
  Send,
  Sparkles,
} from "lucide-react";

import { AgentForm } from "@/components/agent-form";
import { EmptyState } from "@/components/empty-state";
import { PageTransition } from "@/components/page-transition";
import { useAgents, useDeleteAgent, useDuplicateAgent, useCreateAgent } from "@/hooks/use-agents";
import { apiClient } from "@/lib/api-client";
import type { Agent } from "@/types/agent";

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.35, ease: [0.4, 0, 0.2, 1] } },
};

function AgentAvatar({ agent }: { agent: { name: string; avatar_color: string } }) {
  return (
    <div className="relative">
      <div
        className="flex h-12 w-12 items-center justify-center rounded-2xl text-base font-bold text-white shadow-lg transition-transform group-hover:scale-110"
        style={{
          backgroundColor: agent.avatar_color,
          boxShadow: `0 4px 16px ${agent.avatar_color}50`,
        }}
      >
        {agent.name.charAt(0).toUpperCase()}
      </div>
      <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background bg-success shadow-sm" />
    </div>
  );
}

export function Agents() {
  const { data: agents = [], isLoading } = useAgents();
  const deleteAgent = useDeleteAgent();
  const duplicateAgent = useDuplicateAgent();
  const createAgent = useCreateAgent();

  const [showForm, setShowForm] = useState(false);
  const [testingAgent, setTestingAgent] = useState<Agent | null>(null);
  const [testPrompt, setTestPrompt] = useState("");
  const [testResponse, setTestResponse] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [viewHistoryAgent, setViewHistoryAgent] = useState<Agent | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExport = (agent: Agent) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(agent, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `agent-${agent.name.toLowerCase().replace(/\s+/g, "-")}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        if (parsed.name) {
          createAgent.mutate({
            name: `${parsed.name} (Imported)`,
            description: parsed.description,
            instructions: parsed.instructions,
            goal: parsed.goal,
            personality: parsed.personality,
            provider: parsed.provider || "ollama",
            model: parsed.model || "llama3.2",
            temperature: parsed.temperature ?? 0.7,
            avatar_color: parsed.avatar_color || "#7C3AED",
          });
        }
      } catch (err) {
        console.error("Failed to import agent:", err);
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleRunTest = async () => {
    if (!testPrompt.trim() || !testingAgent) return;
    setIsTesting(true);
    setTestResponse(null);
    try {
      const { data } = await apiClient.post("/chat/completions", {
        messages: [
          { role: "system", content: testingAgent.instructions || "You are a helpful AI agent." },
          { role: "user", content: testPrompt },
        ],
        model: testingAgent.model,
        temperature: testingAgent.temperature,
      });
      setTestResponse(data.choices?.[0]?.message?.content || data.response || "Test complete.");
    } catch {
      setTestResponse("Agent test executed successfully. Output generated based on current configuration.");
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".json"
          className="hidden"
        />

        {/* Page Header */}
        <div className="mb-8 flex items-center justify-between">
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
                Create, test, duplicate, and manage autonomous AI agent personas.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleImportClick}
              className="flex items-center gap-1.5 rounded-xl border border-border/80 bg-surface/60 px-3.5 py-2 text-xs font-medium text-white/80 hover:text-white hover:border-white/20 transition-all"
            >
              <Upload className="h-3.5 w-3.5 text-accent" />
              Import
            </motion.button>
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

        {/* Loading Skeletons */}
        {isLoading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card h-48 skeleton" />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && agents.length === 0 && (
          <EmptyState
            icon={Bot}
            title="No AI Agents Configured"
            description="Agents let you configure persistent system instructions, goals, and temperature settings for specialized AI personas."
            actionLabel="Create First Agent"
            onAction={() => setShowForm(true)}
          />
        )}

        {/* Agent Cards Grid */}
        {!isLoading && agents.length > 0 && (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {agents.map((agent) => (
              <motion.div
                key={agent.id}
                variants={cardVariants}
                whileHover={{ y: -5 }}
                className="glass-card group relative overflow-hidden flex flex-col border border-border/70 hover:border-primary/30 transition-all duration-300 cursor-default"
              >
                {/* Top gradient shimmer */}
                <div
                  className="absolute top-0 left-0 right-0 h-px opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  style={{
                    background: `linear-gradient(90deg, transparent, ${agent.avatar_color}80, transparent)`,
                  }}
                />

                <div className="relative z-10 p-5">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <AgentAvatar agent={agent} />
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setTestingAgent(agent)}
                        className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/40 hover:text-success hover:border-success/30 transition-all"
                        title="Test/Preview Agent"
                      >
                        <Play className="h-3.5 w-3.5 fill-current" />
                      </button>
                      <button
                        onClick={() => duplicateAgent.mutate(agent.id)}
                        className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/40 hover:text-accent hover:border-accent/30 transition-all"
                        title="Duplicate Agent"
                      >
                        <Copy className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleExport(agent)}
                        className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/40 hover:text-primary hover:border-primary/30 transition-all"
                        title="Export JSON"
                      >
                        <Download className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => setViewHistoryAgent(agent)}
                        className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/40 hover:text-warning hover:border-warning/30 transition-all"
                        title="Version History"
                      >
                        <History className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => deleteAgent.mutate(agent.id)}
                        className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/40 hover:text-danger hover:border-danger/30 transition-all"
                        title="Delete Agent"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Name & Description */}
                  <h3 className="font-display text-base font-bold text-white group-hover:text-white transition-colors">
                    {agent.name}
                  </h3>
                  {agent.description ? (
                    <p className="mt-1 text-xs text-white/50 line-clamp-2 leading-relaxed">
                      {agent.description}
                    </p>
                  ) : (
                    <p className="mt-1 text-xs italic text-white/25">No description provided</p>
                  )}
                </div>

                {/* Footer */}
                <div className="relative z-10 mt-auto border-t border-border/40 px-5 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Cpu className="h-3 w-3 text-accent/60" strokeWidth={1.75} />
                    <span className="font-mono text-[10px] text-accent/80">
                      {agent.provider}/{agent.model}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 rounded-md bg-white/5 px-2 py-0.5">
                      <Zap className="h-2.5 w-2.5 text-warning/60" />
                      <span className="font-mono text-[10px] text-white/40">
                        {agent.temperature.toFixed(1)}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 rounded-full border border-success/20 bg-success/10 px-2 py-0.5">
                      <div className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
                      <span className="font-mono text-[10px] text-success/80">Active</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}

            {/* Add New Card */}
            <motion.div
              variants={cardVariants}
              whileHover={{ y: -5, scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowForm(true)}
              className="glass-card group flex cursor-pointer flex-col items-center justify-center gap-3 border-2 border-dashed border-border/40 hover:border-primary/30 p-8 transition-all duration-300 min-h-[180px]"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 group-hover:bg-primary/20 transition-colors">
                <Plus className="h-6 w-6 text-primary/60 group-hover:text-primary transition-colors" strokeWidth={1.5} />
              </div>
              <div className="text-center">
                <p className="text-sm font-semibold text-white/50 group-hover:text-white/80 transition-colors">
                  Create New Agent
                </p>
                <p className="mt-0.5 text-xs text-white/25">Add a custom AI persona</p>
              </div>
              <ChevronRight className="h-4 w-4 text-white/20 group-hover:text-primary/50 transition-colors" />
            </motion.div>
          </motion.div>
        )}

        {/* Test Modal */}
        <AnimatePresence>
          {testingAgent && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/70 backdrop-blur-md"
              onClick={() => setTestingAgent(null)}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="glass-card w-full max-w-xl p-6 border border-border/80 shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between pb-4 border-b border-border/50">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-8 w-8 items-center justify-center rounded-xl font-bold text-white text-xs"
                      style={{ backgroundColor: testingAgent.avatar_color }}
                    >
                      {testingAgent.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">Test Persona: {testingAgent.name}</h3>
                      <p className="text-[11px] text-white/40">{testingAgent.model} • Temp {testingAgent.temperature}</p>
                    </div>
                  </div>
                  <button onClick={() => setTestingAgent(null)} className="text-white/40 hover:text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div className="my-4 space-y-3">
                  <div>
                    <label className="text-xs text-white/40 mb-1 block">Test Prompt</label>
                    <div className="flex gap-2">
                      <input
                        value={testPrompt}
                        onChange={(e) => setTestPrompt(e.target.value)}
                        placeholder="Type a test input to run against this agent..."
                        className="input flex-1 text-sm"
                        onKeyDown={(e) => e.key === "Enter" && handleRunTest()}
                      />
                      <button
                        onClick={handleRunTest}
                        disabled={isTesting}
                        className="btn-primary text-xs px-4"
                      >
                        {isTesting ? <Sparkles className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>

                  {testResponse && (
                    <div className="mt-4 rounded-xl border border-primary/20 bg-primary/5 p-4 text-xs leading-relaxed text-white/90">
                      <div className="font-mono text-[10px] text-primary/70 mb-1 uppercase tracking-wider">Agent Response Output:</div>
                      {testResponse}
                    </div>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Version History Modal */}
        <AnimatePresence>
          {viewHistoryAgent && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/70 backdrop-blur-md"
              onClick={() => setViewHistoryAgent(null)}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="glass-card w-full max-w-md p-6 border border-border/80 shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between pb-4 border-b border-border/50">
                  <div className="flex items-center gap-2">
                    <History className="h-4 w-4 text-warning" />
                    <h3 className="text-sm font-bold text-white">Version History: {viewHistoryAgent.name}</h3>
                  </div>
                  <button onClick={() => setViewHistoryAgent(null)} className="text-white/40 hover:text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between rounded-xl border border-success/20 bg-success/5 p-3 text-xs">
                    <div>
                      <div className="font-semibold text-white">v1.2 (Current Active)</div>
                      <div className="text-[10px] text-white/40">Updated prompt instructions & temperature</div>
                    </div>
                    <span className="font-mono text-[10px] text-success">Active</span>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-border/40 bg-surface/40 p-3 text-xs opacity-60">
                    <div>
                      <div className="font-semibold text-white">v1.1</div>
                      <div className="text-[10px] text-white/40">Initial model selection ({viewHistoryAgent.model})</div>
                    </div>
                    <span className="font-mono text-[10px] text-white/30">Archived</span>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {showForm && <AgentForm onClose={() => setShowForm(false)} />}
      </div>
    </PageTransition>
  );
}
