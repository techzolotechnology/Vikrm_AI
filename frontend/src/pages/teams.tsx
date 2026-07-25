import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, ChevronRight, Play, Plus, Trash2, Users, XCircle, Sparkles, Loader2 } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageTransition } from "@/components/page-transition";
import { TeamForm } from "@/components/team-form";
import {
  useAgentTeamRuns,
  useAgentTeams,
  useDeleteAgentTeam,
  useRunAgentTeam,
} from "@/hooks/use-agent-teams";
import { useAgents } from "@/hooks/use-agents";
import { cn } from "@/lib/utils";

export function Teams() {
  const { data: teams = [], isLoading } = useAgentTeams();
  const { data: agents = [] } = useAgents();
  const deleteTeam = useDeleteAgentTeam();
  const [showForm, setShowForm] = useState(false);
  const [activeTeamId, setActiveTeamId] = useState<number | null>(null);
  const [task, setTask] = useState("");

  const activeTeam = teams.find((t) => t.id === activeTeamId);
  const runTeam = useRunAgentTeam(activeTeamId ?? -1);
  const { data: runs = [] } = useAgentTeamRuns(activeTeamId);
  const latestRun = runTeam.data ?? runs[0];

  const agentName = (id: number) => agents.find((a) => a.id === id)?.name ?? `Agent #${id}`;
  const agentColor = (id: number) => agents.find((a) => a.id === id)?.avatar_color ?? "#7C3AED";

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        {/* Page Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className="page-icon-wrap"
              style={{ background: "linear-gradient(135deg, rgba(236,72,153,0.2) 0%, rgba(219,39,119,0.1) 100%)", borderColor: "rgba(236,72,153,0.3)" }}
            >
              <Users className="h-5 w-5" style={{ color: "#EC4899" }} strokeWidth={1.75} />
            </div>
            <div>
              <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
                Orchestration
              </span>
              <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                Agent Teams
              </h1>
              <p className="text-sm text-white/40">
                Multi-agent orchestration with dynamic task delegation.
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
              className="flex items-center gap-2 rounded-xl bg-gradient-brand px-4 py-2.5 text-xs font-bold text-white shadow-glow-sm transition-all"
            >
              <Plus className="h-4 w-4" strokeWidth={2} />
              Create Team
            </motion.button>
          </div>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="glass-card h-64 skeleton" />
        )}

        {/* Empty */}
        {!isLoading && teams.length === 0 && (
          <EmptyState
            icon={Users}
            title="No Agent Teams"
            description="Form teams by assigning a Manager Agent and Member Agents to solve multi-step problems collaboratively."
            actionLabel="Create First Team"
            onAction={() => setShowForm(true)}
          />
        )}

        {/* Main Layout */}
        {teams.length > 0 && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-[280px_1fr]">
            {/* Team List */}
            <div className="space-y-2">
              {teams.map((team) => (
                <motion.div
                  key={team.id}
                  whileHover={{ x: 2 }}
                  onClick={() => setActiveTeamId(team.id)}
                  className={cn(
                    "glass-card group flex cursor-pointer items-center justify-between gap-2 p-3.5 transition-all duration-200 border",
                    activeTeamId === team.id
                      ? "border-pink-400/40 bg-pink-400/10 shadow-sm"
                      : "border-border/70 hover:border-white/15",
                  )}
                >
                  {activeTeamId === team.id && (
                    <motion.div
                      layoutId="activeTeam"
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-8 rounded-r-full bg-gradient-to-b from-pink-400 to-rose-500"
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                  <div className="min-w-0">
                    <p className="truncate text-sm font-bold text-white">{team.name}</p>
                    <p className="truncate font-mono text-[11px] text-white/35 mt-0.5">
                      {team.member_agent_ids.length + 1} agents
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteTeam.mutate(team.id);
                        if (activeTeamId === team.id) setActiveTeamId(null);
                      }}
                      className="flex h-6 w-6 items-center justify-center rounded-lg text-white/20 hover:text-danger transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                    </button>
                    <ChevronRight className={cn(
                      "h-4 w-4 transition-colors",
                      activeTeamId === team.id ? "text-pink-400" : "text-white/20",
                    )} />
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Detail Panel */}
            <AnimatePresence mode="wait">
              {activeTeam ? (
                <motion.div
                  key={activeTeam.id}
                  initial={{ opacity: 0, x: 16 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 16 }}
                  transition={{ duration: 0.25 }}
                  className="glass-card border border-border/70 p-6 shadow-2xl"
                >
                  <h2 className="font-display text-lg font-bold text-white">{activeTeam.name}</h2>
                  {activeTeam.description && (
                    <p className="mt-1 text-sm text-white/50">{activeTeam.description}</p>
                  )}

                  {/* Agent badges */}
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="flex items-center gap-1.5 rounded-full border border-pink-400/30 bg-pink-400/15 px-3 py-1 font-mono text-[11px] font-semibold text-pink-300">
                      <div
                        className="h-4 w-4 rounded-full flex items-center justify-center text-[9px] font-bold text-white"
                        style={{ backgroundColor: agentColor(activeTeam.manager_agent_id) }}
                      >
                        M
                      </div>
                      {agentName(activeTeam.manager_agent_id)}
                    </span>
                    {activeTeam.member_agent_ids.map((id) => (
                      <span
                        key={id}
                        className="flex items-center gap-1.5 rounded-full border border-border/60 bg-white/5 px-3 py-1 font-mono text-[11px] text-white/60"
                      >
                        <div
                          className="h-4 w-4 rounded-full flex items-center justify-center text-[9px] font-bold text-white"
                          style={{ backgroundColor: agentColor(id) }}
                        >
                          {agentName(id).charAt(0)}
                        </div>
                        {agentName(id)}
                      </span>
                    ))}
                  </div>

                  {/* Task input */}
                  <div className="mt-6 flex gap-2">
                    <input
                      value={task}
                      onChange={(e) => setTask(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && task.trim() && runTeam.mutate(task.trim())}
                      placeholder="Describe a goal for this team to complete..."
                      className="input text-sm flex-1"
                    />
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => task.trim() && runTeam.mutate(task.trim())}
                      disabled={runTeam.isPending || !task.trim()}
                      className="flex shrink-0 items-center gap-2 rounded-xl bg-gradient-brand px-5 text-xs font-bold text-white shadow-glow-sm disabled:opacity-40 transition-all"
                    >
                      {runTeam.isPending ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Play className="h-3.5 w-3.5" strokeWidth={2} />
                      )}
                      {runTeam.isPending ? "Running..." : "Run Team"}
                    </motion.button>
                  </div>

                  {/* Execution Results */}
                  <AnimatePresence>
                    {latestRun && (
                      <motion.div
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-6 space-y-3 border-t border-border/40 pt-5"
                      >
                        <div className="flex items-center gap-2">
                          {latestRun.status === "completed" ? (
                            <CheckCircle2 className="h-4 w-4 text-success" />
                          ) : (
                            <XCircle className="h-4 w-4 text-danger" />
                          )}
                          <span className="text-sm font-semibold text-white/80">
                            {latestRun.status === "completed" ? "Completed" : "Failed"}
                          </span>
                          <span className="font-mono text-[11px] text-white/30">
                            · {latestRun.steps.length} subtask{latestRun.steps.length !== 1 ? "s" : ""}
                          </span>
                        </div>

                        <div className="space-y-2">
                          {latestRun.steps.map((step, i) => (
                            <motion.div
                              key={i}
                              initial={{ opacity: 0, x: -8 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: i * 0.06 }}
                              className="flex items-start gap-3 rounded-xl border border-border/50 bg-surface/40 p-3.5"
                            >
                              <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[9px] font-bold"
                                style={{
                                  borderColor: step.status === "success" ? "rgba(34,197,94,0.4)" : "rgba(239,68,68,0.4)",
                                  color: step.status === "success" ? "#22C55E" : "#EF4444",
                                  background: step.status === "success" ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
                                }}>
                                {i + 1}
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-2 mb-0.5">
                                  <span className="text-xs font-bold text-white">{step.agent_name}</span>
                                  {step.status === "success" ? (
                                    <CheckCircle2 className="h-3 w-3 text-success" />
                                  ) : (
                                    <XCircle className="h-3 w-3 text-danger" />
                                  )}
                                </div>
                                <p className="font-mono text-[10px] text-white/35 mb-1">{step.subtask}</p>
                                <p className="text-xs text-white/75 leading-relaxed">
                                  {step.status === "success" ? step.output : step.error}
                                </p>
                              </div>
                            </motion.div>
                          ))}
                        </div>

                        {latestRun.final_output && (
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.2 }}
                            className="rounded-xl border border-primary/25 bg-primary/8 px-5 py-4 shadow-glow-sm"
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
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="glass-card flex flex-col items-center justify-center gap-3 border border-border/50 p-12 text-center"
                >
                  <Users className="h-10 w-10 text-white/10" strokeWidth={1} />
                  <p className="text-sm text-white/30">Select a team to view details and execute tasks.</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {showForm && <TeamForm onClose={() => setShowForm(false)} />}
      </div>
    </PageTransition>
  );
}
