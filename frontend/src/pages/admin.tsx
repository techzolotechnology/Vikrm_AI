import { motion } from "framer-motion";
import {
  Bot,
  FileText,
  MessageSquare,
  Shield,
  ShieldOff,
  Users,
  Workflow,
  Wrench,
  Activity,
  TrendingUp,
} from "lucide-react";

import { PageTransition } from "@/components/page-transition";
import { useAdminUsers, useSystemStats, useUpdateUser } from "@/hooks/use-admin";
import { useAuthStore } from "@/store/use-auth-store";
import { cn } from "@/lib/utils";

export function Admin() {
  const currentUser = useAuthStore((state) => state.user);
  const { data: stats } = useSystemStats();
  const { data: users = [], isLoading } = useAdminUsers();
  const updateUser = useUpdateUser();

  const statCards = stats
    ? [
        { icon: Users, label: "Users", value: `${stats.active_users}/${stats.total_users}`, sub: "active/total", color: "#EC4899" },
        { icon: MessageSquare, label: "Conversations", value: stats.total_conversations, color: "#7C3AED" },
        { icon: Bot, label: "Agents", value: stats.total_agents, color: "#22D3EE" },
        { icon: Workflow, label: "Workflows", value: stats.total_workflows, color: "#06B6D4" },
        { icon: FileText, label: "Documents", value: stats.total_documents, color: "#F59E0B" },
        { icon: Wrench, label: "Tool Runs", value: stats.total_tool_executions, color: "#F97316" },
      ]
    : [];

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        {/* Page Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className="page-icon-wrap"
              style={{ background: "linear-gradient(135deg, rgba(239,68,68,0.2) 0%, rgba(220,38,38,0.1) 100%)", borderColor: "rgba(239,68,68,0.3)" }}
            >
              <Shield className="h-5 w-5" style={{ color: "#EF4444" }} strokeWidth={1.75} />
            </div>
            <div>
              <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
                Administrator
              </span>
              <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                System Control
              </h1>
              <p className="text-sm text-white/40">
                User management, role access, and platform telemetry.
              </p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        {statCards.length > 0 && (
          <div className="mb-8">
            <div className="mb-3 flex items-center gap-2">
              <TrendingUp className="h-3.5 w-3.5 text-white/30" />
              <span className="font-mono text-[10px] uppercase tracking-wider text-white/30">
                Platform Telemetry
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-6">
              {statCards.map((card, index) => (
                <motion.div
                  key={card.label}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  whileHover={{ y: -3 }}
                  transition={{ delay: index * 0.05, duration: 0.35 }}
                  className="stat-card group relative overflow-hidden"
                >
                  <div
                    className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl"
                    style={{ background: `radial-gradient(ellipse at 30% 30%, ${card.color}15 0%, transparent 70%)` }}
                  />
                  <div className="relative z-10">
                    <div
                      className="flex h-8 w-8 items-center justify-center rounded-xl"
                      style={{ background: `${card.color}15`, border: `1px solid ${card.color}25` }}
                    >
                      <card.icon className="h-4 w-4" style={{ color: card.color }} strokeWidth={1.75} />
                    </div>
                    <p className="mt-3 font-display text-xl font-bold text-white">{card.value}</p>
                    <p className="mt-0.5 font-mono text-[10px] text-white/40">{card.label}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* User Management Table */}
        <div className="mb-4 flex items-center gap-2">
          <Activity className="h-4 w-4 text-white/30" />
          <h2 className="font-display text-sm font-semibold text-white/70">User Accounts</h2>
          {users.length > 0 && (
            <span className="ml-auto font-mono text-[11px] text-white/30">
              {users.length} registered
            </span>
          )}
        </div>

        <div className="glass-card overflow-hidden border border-border/70 shadow-2xl">
          {/* Table header */}
          <div className="hidden md:grid grid-cols-[1fr_auto] border-b border-border/50 px-5 py-3">
            <span className="font-mono text-[10px] uppercase tracking-wider text-white/30">User</span>
            <span className="font-mono text-[10px] uppercase tracking-wider text-white/30">Actions</span>
          </div>

          {isLoading && (
            <div className="p-5 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 skeleton rounded-xl" />
              ))}
            </div>
          )}

          {!isLoading && users.map((user, index) => {
            const isSelf = user.id === currentUser?.id;
            return (
              <motion.div
                key={user.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.04 }}
                className="flex items-center justify-between gap-4 border-b border-border/40 px-5 py-3.5 last:border-b-0 hover:bg-white/[0.025] transition-colors"
              >
                {/* User info */}
                <div className="flex min-w-0 items-center gap-3.5">
                  {user.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt=""
                      className="h-9 w-9 shrink-0 rounded-full border border-primary/30 object-cover"
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-xs font-bold text-white shadow-glow-sm">
                      {(user.full_name ?? user.email).charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div className="min-w-0">
                    <p className="flex items-center gap-2 truncate text-sm font-semibold text-white">
                      {user.full_name ?? user.email.split("@")[0]}
                      {isSelf && (
                        <span className="rounded-full bg-primary/20 border border-primary/25 px-2 py-0.5 font-mono text-[9px] font-semibold text-primary">
                          you
                        </span>
                      )}
                    </p>
                    <p className="truncate font-mono text-[11px] text-white/35">{user.email}</p>
                  </div>
                </div>

                {/* Badges + Actions */}
                <div className="flex shrink-0 items-center gap-2.5">
                  <span
                    className={cn(
                      "rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-bold",
                      user.role === "admin"
                        ? "bg-primary/20 text-primary border-primary/30"
                        : "bg-white/5 text-white/40 border-white/10",
                    )}
                  >
                    {user.role}
                  </span>
                  <span
                    className={cn(
                      "flex items-center gap-1 rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-bold",
                      user.is_active
                        ? "bg-success/15 text-success border-success/25"
                        : "bg-danger/15 text-danger border-danger/25",
                    )}
                  >
                    <div className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      user.is_active ? "bg-success animate-pulse" : "bg-danger",
                    )} />
                    {user.is_active ? "active" : "inactive"}
                  </span>

                  <div className="h-4 w-px bg-border/60" />

                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() =>
                      updateUser.mutate({
                        userId: user.id,
                        role: user.role === "admin" ? "user" : "admin",
                      })
                    }
                    disabled={isSelf || updateUser.isPending}
                    title={isSelf ? "You cannot change your own role" : "Toggle admin role"}
                    className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/40 transition-all hover:border-primary/40 hover:text-white disabled:opacity-20"
                  >
                    {user.role === "admin" ? (
                      <ShieldOff className="h-3.5 w-3.5 text-danger" strokeWidth={1.75} />
                    ) : (
                      <Shield className="h-3.5 w-3.5 text-accent" strokeWidth={1.75} />
                    )}
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => updateUser.mutate({ userId: user.id, is_active: !user.is_active })}
                    disabled={isSelf || updateUser.isPending}
                    title={isSelf ? "You cannot deactivate yourself" : "Toggle active status"}
                    className={cn(
                      "rounded-xl border px-3 py-1.5 text-xs font-semibold transition-all disabled:opacity-20",
                      user.is_active
                        ? "border-danger/40 text-danger hover:bg-danger/10"
                        : "border-success/40 text-success hover:bg-success/10",
                    )}
                  >
                    {user.is_active ? "Deactivate" : "Activate"}
                  </motion.button>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </PageTransition>
  );
}
