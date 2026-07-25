import { useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Bot,
  Brain,
  Database,
  FileText,
  MessageSquare,

  Server,
  Sparkles,
  Users,
  Workflow,
  Wrench,
  Zap,
  ArrowUpRight,
  Activity,
} from "lucide-react";

import { ActivityFeed } from "@/components/activity-feed";
import { CircuitTrace } from "@/components/circuit-trace";
import { PageTransition } from "@/components/page-transition";
import { RunStatusChart } from "@/components/run-status-chart";
import { ServiceCard } from "@/components/service-card";
import { StatCard } from "@/components/stat-card";
import { SystemPulse } from "@/components/system-pulse";
import { useDashboardStats, useRecentActivity } from "@/hooks/use-analytics";
import { useHealth, useReadiness, useVersion } from "@/hooks/use-system-health";
import { useSystemStatusStore } from "@/store/use-system-status-store";
import { useAuthStore } from "@/store/use-auth-store";

const quickActions = [
  { label: "New Chat", path: "/chat", icon: MessageSquare, color: "from-violet-500/20 to-indigo-600/10", iconColor: "#7C3AED" },
  { label: "New Agent", path: "/agents", icon: Bot, color: "from-cyan-500/20 to-blue-500/10", iconColor: "#22D3EE" },
  { label: "Upload Doc", path: "/documents", icon: FileText, color: "from-emerald-500/20 to-teal-500/10", iconColor: "#22C55E" },
  { label: "Build Workflow", path: "/workflows", icon: Workflow, color: "from-amber-500/20 to-orange-500/10", iconColor: "#F59E0B" },
  { label: "Agent Teams", path: "/teams", icon: Users, color: "from-pink-500/20 to-rose-500/10", iconColor: "#EC4899" },
];

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
};

export function Dashboard() {
  const health = useHealth();
  const readiness = useReadiness();
  const version = useVersion();
  const markChecked = useSystemStatusStore((state) => state.markChecked);
  const { data: stats } = useDashboardStats();
  const { data: activity = [] } = useRecentActivity();
  const user = useAuthStore((state) => state.user);

  const isLoading = health.isLoading || readiness.isLoading;
  const isReady = readiness.data?.status === "ready";

  useEffect(() => {
    if (readiness.isSuccess) {
      markChecked();
    }
  }, [readiness.isSuccess, readiness.dataUpdatedAt, markChecked]);

  return (
    <PageTransition>
      <div className="aurora-bg relative min-h-screen bg-background">
        <div className="relative z-10 px-8 py-8 md:px-12">

          {/* Header Row */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="mb-8 flex items-center justify-between"
          >
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Activity className="h-4 w-4 text-accent" strokeWidth={1.75} />
                <span className="font-mono text-[11px] text-white/40 uppercase tracking-widest">
                  Executive Control Center
                </span>
              </div>
              <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                Welcome back{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
              </h1>
              <p className="mt-0.5 text-sm text-white/40">
                Your AI infrastructure is running smoothly.
              </p>
            </div>

            <SystemPulse isReady={isReady} isLoading={isLoading} />
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="mb-8"
          >
            <div className="mb-3 flex items-center gap-2">
              <Zap className="h-3.5 w-3.5 text-accent" />
              <h2 className="font-display text-xs font-semibold uppercase tracking-wider text-white/40">
                Quick Actions
              </h2>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
              {quickActions.map((action) => (
                <motion.div key={action.label} variants={itemVariants}>
                  <Link to={action.path}>
                    <motion.div
                      whileHover={{ y: -4, scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      className={`relative overflow-hidden glass-card flex items-center justify-between p-4 border border-border/60 hover:border-primary/30 bg-gradient-to-br ${action.color} group transition-all duration-300 cursor-pointer`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="flex h-8 w-8 items-center justify-center rounded-xl transition-transform group-hover:scale-110"
                          style={{
                            background: `${action.iconColor}18`,
                            border: `1px solid ${action.iconColor}30`,
                          }}
                        >
                          <action.icon className="h-4 w-4" style={{ color: action.iconColor }} strokeWidth={1.75} />
                        </div>
                        <span className="text-xs font-semibold text-white/90 group-hover:text-white transition-colors">
                          {action.label}
                        </span>
                      </div>
                      <ArrowUpRight className="h-3.5 w-3.5 text-white/20 group-hover:text-white/60 transition-colors" />
                    </motion.div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Stats Grid */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.4 }}
            className="mb-8"
          >
            <div className="mb-3 flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-accent" />
              <h2 className="font-display text-xs font-semibold uppercase tracking-wider text-white/40">
                Platform Statistics
              </h2>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-6">
              <StatCard
                index={0}
                icon={MessageSquare}
                label="Conversations"
                value={stats?.total_conversations ?? 0}
                subtext={stats ? `${stats.total_messages} messages` : undefined}
                color="#7C3AED"
              />
              <StatCard
                index={1}
                icon={Bot}
                label="Agents"
                value={stats?.total_agents ?? 0}
                color="#22D3EE"
              />
              <StatCard
                index={2}
                icon={Users}
                label="Teams"
                value={stats?.total_teams ?? 0}
                color="#EC4899"
              />
              <StatCard
                index={3}
                icon={Brain}
                label="Memories"
                value={stats?.total_memories ?? 0}
                color="#22C55E"
              />
              <StatCard
                index={4}
                icon={FileText}
                label="Documents"
                value={stats?.total_documents ?? 0}
                subtext={stats ? `${stats.documents_ready} ready` : undefined}
                color="#F59E0B"
              />
              <StatCard
                index={5}
                icon={Wrench}
                label="Tool Runs"
                value={stats?.total_tool_executions ?? 0}
                subtext={stats ? `${stats.tool_executions_success} succeeded` : undefined}
                color="#F97316"
              />
            </div>
          </motion.div>

          {/* Charts + Activity */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.4 }}
            className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3"
          >
            <RunStatusChart
              title="Workflow Telemetry"
              data={stats?.workflow_runs ?? { completed: 0, failed: 0, running: 0 }}
            />
            <RunStatusChart
              title="Team Orchestration"
              data={stats?.team_runs ?? { completed: 0, failed: 0, running: 0 }}
            />

            {/* Workflows saved card */}
            <motion.div
              whileHover={{ y: -3 }}
              className="glass-card group relative overflow-hidden p-5 border border-border/80 hover:border-primary/20 transition-all duration-300"
            >
              <div
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl"
                style={{
                  background: "radial-gradient(ellipse at 50% 0%, rgba(34,211,238,0.08) 0%, transparent 65%)",
                }}
              />
              <div className="relative z-10">
                <div className="flex items-center justify-between">
                  <h3 className="font-display text-xs font-semibold text-white/60">Saved Workflows</h3>
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent/10 border border-accent/20">
                    <Workflow className="h-4 w-4 text-accent" strokeWidth={1.75} />
                  </div>
                </div>
                <p className="mt-4 font-display text-3xl font-bold tracking-tight text-white">
                  {stats?.total_workflows ?? "—"}
                </p>
                <p className="mt-1 font-mono text-[11px] text-white/30">DAG execution pipelines</p>

                <Link
                  to="/workflows"
                  className="mt-4 inline-flex items-center gap-1.5 text-xs text-accent/70 hover:text-accent transition-colors"
                >
                  <span>View all workflows</span>
                  <ArrowUpRight className="h-3 w-3" />
                </Link>
              </div>
            </motion.div>
          </motion.div>

          {/* Activity Feed */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35, duration: 0.4 }}
            className="mb-8 glass-card border border-border/80 p-6 shadow-2xl"
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="flex items-center gap-2 font-display text-sm font-semibold text-white">
                <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-accent/10 border border-accent/20">
                  <Activity className="h-3.5 w-3.5 text-accent" />
                </div>
                Live Activity Stream
              </h2>
              <div className="flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
                <span className="font-mono text-[10px] text-white/30">Live</span>
              </div>
            </div>
            <ActivityFeed items={activity} />
          </motion.div>

          {/* Infrastructure Health */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45, duration: 0.4 }}
            className="relative"
          >
            <div className="mb-3 flex items-center gap-2">
              <Server className="h-3.5 w-3.5 text-accent" />
              <h2 className="font-display text-xs font-semibold uppercase tracking-wider text-white/40">
                Infrastructure Health
              </h2>
            </div>
            <CircuitTrace />
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <ServiceCard
                index={0}
                icon={Server}
                name="FastAPI Server"
                description={
                  health.isError
                    ? "Backend unreachable"
                    : `v${health.data?.version ?? "—"} · ${health.data?.status ?? "checking"}`
                }
                status={health.isLoading ? "checking" : health.isError ? "down" : "up"}
              />
              <ServiceCard
                index={1}
                icon={Database}
                name="MySQL Store"
                description="Relational database cluster"
                status={readiness.isLoading ? "checking" : (readiness.data?.database ?? "down")}
              />
              <ServiceCard
                index={2}
                icon={Zap}
                name="Redis Engine"
                description="Task broker & rate limiter"
                status={readiness.isLoading ? "checking" : (readiness.data?.redis ?? "down")}
              />
            </div>
          </motion.div>

          {/* Footer */}
          <div className="mt-10 flex items-center justify-between border-t border-border/30 pt-4 font-mono text-[10px] text-white/20">
            <span>ENV: {version.data?.environment?.toUpperCase() ?? "DEVELOPMENT"}</span>
            <span>{version.data?.app_name ?? "Vikrm Engine"} v{version.data?.version ?? "0.1.0"}</span>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
