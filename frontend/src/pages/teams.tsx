import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  Crown,
  Loader2,
  Play,
  Plus,
  Sparkles,
  Trash2,
  Users,
  XCircle,
  Bot,
  Zap,
  Clock,
  ChevronDown,
  ChevronUp,
  RotateCcw,
} from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageTransition } from "@/components/page-transition";
import { TeamForm } from "@/components/team-form";
import { Tooltip } from "@/components/ui/tooltip";
import {
  useAgentTeamRuns,
  useAgentTeams,
  useDeleteAgentTeam,
  useRunAgentTeam,
} from "@/hooks/use-agent-teams";
import { useAgents } from "@/hooks/use-agents";
import { cn } from "@/lib/utils";
import type { AgentTeam } from "@/types/agent-team";

// ─── Team Card ───────────────────────────────────────────────────────────────

interface TeamCardProps {
  team: AgentTeam;
  agents: ReturnType<typeof useAgents>["data"];
  onDelete: (id: number) => void;
}

function TeamCard({ team, agents = [], onDelete }: TeamCardProps) {
  const [task, setTask] = useState("");
  const [expanded, setExpanded] = useState(false);
  const runTeam = useRunAgentTeam(team.id);
  const { data: runs = [] } = useAgentTeamRuns(team.id);
  const latestRun = runTeam.data ?? runs[0];

  const agentById = (id: number) => agents.find((a) => a.id === id);
  const manager = agentById(team.manager_agent_id);
  const members = team.member_agent_ids.map((id) => agentById(id)).filter(Boolean);

  const handleRun = () => {
    if (!task.trim()) return;
    runTeam.mutate(task.trim());
  };

  const statusColor = latestRun?.status === "completed"
    ? "text-success border-success/30 bg-success/10"
    : latestRun?.status === "failed"
      ? "text-danger border-danger/30 bg-danger/10"
      : latestRun?.status === "running"
        ? "text-accent border-accent/30 bg-accent/10"
        : "text-white/30 border-border bg-white/5";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.3 }}
      className="glass-card border border-border/70 overflow-hidden hover:border-pink-400/20 transition-all duration-300 group"
    >
      {/* Hover shimmer */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-pink-400/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Card Header */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          {/* Team icon + name */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-pink-400/25 bg-pink-400/10">
              <Users className="h-5 w-5 text-pink-400" strokeWidth={1.75} />
            </div>
            <div className="min-w-0">
              <h3 className="font-display text-sm font-bold text-white truncate">{team.name}</h3>
              {team.description && (
                <p className="text-xs text-white/45 mt-0.5 line-clamp-1">{team.description}</p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1.5 shrink-0">
            {latestRun && (
              <span className={cn("flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-[10px]", statusColor)}>
                {latestRun.status === "running" && (
                  <motion.span
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                    className="inline-block"
                  >
                    <RotateCcw className="h-2.5 w-2.5" />
                  </motion.span>
                )}
                {latestRun.status === "completed" && <CheckCircle2 className="h-2.5 w-2.5" />}
                {latestRun.status === "failed" && <XCircle className="h-2.5 w-2.5" />}
                {latestRun.status}
              </span>
            )}
            <Tooltip content="Delete team" side="top">
              <button
                onClick={() => onDelete(team.id)}
                className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 text-white/20 hover:text-danger hover:border-danger/30 hover:bg-danger/10 transition-all opacity-0 group-hover:opacity-100"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </Tooltip>
          </div>
        </div>

        {/* Agent Badges */}
        <div className="mt-4 flex flex-wrap gap-2">
          {/* Manager */}
          {manager && (
            <div className="flex items-center gap-1.5 rounded-xl border border-pink-400/30 bg-pink-400/10 px-2.5 py-1">
              <div
                className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[8px] font-bold text-white"
                style={{ backgroundColor: manager.avatar_color }}
              >
                <Crown className="h-2.5 w-2.5" />
              </div>
              <span className="font-mono text-[11px] font-semibold text-pink-300">{manager.name}</span>
              <span className="text-[9px] text-pink-400/60 uppercase tracking-wider">Manager</span>
            </div>
          )}
          {/* Members */}
          {members.map((member) =>
            member ? (
              <div
                key={member.id}
                className="flex items-center gap-1.5 rounded-xl border border-border/50 bg-white/5 px-2.5 py-1"
              >
                <div
                  className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[9px] font-bold text-white"
                  style={{ backgroundColor: member.avatar_color }}
                >
                  {member.name.charAt(0)}
                </div>
                <span className="font-mono text-[11px] text-white/65">{member.name}</span>
              </div>
            ) : null,
          )}
        </div>

        {/* Stats row */}
        <div className="mt-3 flex items-center gap-4 text-[11px] font-mono text-white/30">
          <span className="flex items-center gap-1">
            <Bot className="h-3 w-3" />
            {team.member_agent_ids.length + 1} agents
          </span>
          {runs.length > 0 && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {runs.length} run{runs.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      {/* Task Runner */}
      <div className="border-t border-border/40 bg-surface/20 p-4">
        <div className="flex gap-2">
          <input
            value={task}
            onChange={(e) => setTask(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && task.trim() && handleRun()}
            placeholder="Describe a goal for this team..."
            className="input text-xs flex-1 bg-background/60"
          />
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRun}
            disabled={runTeam.isPending || !task.trim()}
            className="flex shrink-0 items-center gap-1.5 rounded-xl bg-gradient-to-r from-pink-500 to-rose-500 px-4 text-xs font-bold text-white shadow-lg disabled:opacity-40 transition-all"
          >
            {runTeam.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" strokeWidth={2} />
            )}
            {runTeam.isPending ? "Running..." : "Run"}
          </motion.button>
        </div>
      </div>

      {/* Execution Results */}
      <AnimatePresence>
        {latestRun && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-border/40 overflow-hidden"
          >
            {/* Result header */}
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex w-full items-center justify-between px-4 py-3 text-xs hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-2">
                {latestRun.status === "completed" ? (
                  <CheckCircle2 className="h-4 w-4 text-success" />
                ) : latestRun.status === "failed" ? (
                  <XCircle className="h-4 w-4 text-danger" />
                ) : (
                  <Loader2 className="h-4 w-4 text-accent animate-spin" />
                )}
                <span className="font-semibold text-white/80">
                  {latestRun.status === "completed" ? "Task Completed" : latestRun.status === "failed" ? "Task Failed" : "Running..."}
                </span>
                <span className="font-mono text-[10px] text-white/30">
                  · {latestRun.steps?.length ?? 0} subtasks
                </span>
              </div>
              {expanded ? (
                <ChevronUp className="h-3.5 w-3.5 text-white/30" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5 text-white/30" />
              )}
            </button>

            <AnimatePresence>
              {expanded && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="px-4 pb-4 space-y-2.5"
                >
                  {/* Step results */}
                  {latestRun.steps?.map((step, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-start gap-3 rounded-xl border border-border/50 bg-surface/40 p-3"
                    >
                      <div
                        className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[9px] font-bold"
                        style={{
                          borderColor: step.status === "success" ? "rgba(34,197,94,0.4)" : "rgba(239,68,68,0.4)",
                          color: step.status === "success" ? "#22C55E" : "#EF4444",
                          background: step.status === "success" ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
                        }}
                      >
                        {i + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold text-white">{step.agent_name}</span>
                          {step.status === "success" ? (
                            <CheckCircle2 className="h-3 w-3 text-success" />
                          ) : (
                            <XCircle className="h-3 w-3 text-danger" />
                          )}
                        </div>
                        <p className="font-mono text-[10px] text-white/35 mb-1">{step.subtask}</p>
                        <p className="text-xs text-white/70 leading-relaxed">
                          {step.status === "success" ? step.output : step.error}
                        </p>
                      </div>
                    </motion.div>
                  ))}

                  {/* Final output */}
                  {latestRun.final_output && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 }}
                      className="rounded-xl border border-primary/25 bg-primary/8 px-4 py-3 shadow-glow-sm"
                    >
                      <div className="mb-2 flex items-center gap-1.5">
                        <Sparkles className="h-3.5 w-3.5 text-accent" />
                        <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-accent">
                          Synthesized Output
                        </span>
                      </div>
                      <p className="whitespace-pre-wrap text-sm text-white/85 leading-relaxed">
                        {latestRun.final_output}
                      </p>
                    </motion.div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ─── Template Suggestions ────────────────────────────────────────────────────

const TEMPLATES = [
  {
    name: "Research Team",
    description: "Research → Summarize → Report",
    icon: "🔬",
    color: "#7C3AED",
  },
  {
    name: "Code Review Team",
    description: "Review → Test → Document",
    icon: "💻",
    color: "#22D3EE",
  },
  {
    name: "Content Creation",
    description: "Write → Edit → Publish",
    icon: "✍️",
    color: "#22C55E",
  },
];

// ─── Main Page ────────────────────────────────────────────────────────────────

export function Teams() {
  const { data: teams = [], isLoading } = useAgentTeams();
  const { data: agents = [] } = useAgents();
  const deleteTeam = useDeleteAgentTeam();
  const [showForm, setShowForm] = useState(false);

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        {/* Page Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className="page-icon-wrap"
              style={{
                background: "linear-gradient(135deg, rgba(236,72,153,0.2) 0%, rgba(219,39,119,0.1) 100%)",
                borderColor: "rgba(236,72,153,0.3)",
              }}
            >
              <Users className="h-5 w-5" style={{ color: "#EC4899" }} strokeWidth={1.75} />
            </div>
            <div>
              <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
                Multi-Agent Orchestration
              </span>
              <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                Agent Teams
              </h1>
              <p className="text-sm text-white/40">
                Collaborate multiple agents on complex tasks with dynamic role delegation.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {teams.length > 0 && (
              <span className="font-mono text-[11px] text-white/30">
                {teams.length} team{teams.length !== 1 ? "s" : ""}
              </span>
            )}
            <motion.button
              whileHover={{ scale: 1.03, y: -1 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-pink-500 to-rose-500 px-4 py-2.5 text-xs font-bold text-white shadow-lg transition-all"
            >
              <Plus className="h-4 w-4" strokeWidth={2} />
              Create Team
            </motion.button>
          </div>
        </div>

        {/* Templates bar (when no teams) */}
        {!isLoading && teams.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <p className="mb-3 font-mono text-[11px] uppercase tracking-wider text-white/30 flex items-center gap-2">
              <Zap className="h-3.5 w-3.5" />
              Quick Templates
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
              {TEMPLATES.map((tmpl) => (
                <motion.button
                  key={tmpl.name}
                  whileHover={{ y: -2, scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowForm(true)}
                  className="glass-card flex items-center gap-3 p-4 border border-border/60 hover:border-pink-400/30 text-left transition-all group cursor-pointer"
                >
                  <span className="text-2xl">{tmpl.icon}</span>
                  <div>
                    <p className="text-xs font-bold text-white group-hover:text-pink-300 transition-colors">{tmpl.name}</p>
                    <p className="text-[11px] text-white/40 mt-0.5">{tmpl.description}</p>
                  </div>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Loading skeletons */}
        {isLoading && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card h-64 skeleton border border-border/50" />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && teams.length === 0 && (
          <EmptyState
            icon={Users}
            title="No Agent Teams Yet"
            description="Create your first team by assigning a Manager Agent and Member Agents to solve complex multi-step tasks collaboratively."
            actionLabel="Create First Team"
            onAction={() => setShowForm(true)}
          />
        )}

        {/* Team Cards Grid */}
        {teams.length > 0 && (
          <AnimatePresence>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {teams.map((team) => (
                <TeamCard
                  key={team.id}
                  team={team}
                  agents={agents}
                  onDelete={(id) => deleteTeam.mutate(id)}
                />
              ))}
            </div>
          </AnimatePresence>
        )}

        {/* Create Form Modal */}
        {showForm && <TeamForm onClose={() => setShowForm(false)} />}
      </div>
    </PageTransition>
  );
}
