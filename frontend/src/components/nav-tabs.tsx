import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Brain,
  ChevronLeft,
  ChevronRight,
  FileText,
  LayoutDashboard,
  MessageSquare,
  Search,
  Shield,
  Users,
  Workflow,
  Wrench,
  Zap,
} from "lucide-react";

import { CommandPalette } from "@/components/command-palette";
import { UserMenu } from "@/components/user-menu";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/use-auth-store";

const TABS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true, adminOnly: false, color: "#7C3AED" },
  { to: "/chat", label: "Chat", icon: MessageSquare, end: false, adminOnly: false, color: "#22D3EE" },
  { to: "/agents", label: "Agents", icon: Bot, end: false, adminOnly: false, color: "#8B5CF6" },
  { to: "/teams", label: "Teams", icon: Users, end: false, adminOnly: false, color: "#EC4899" },
  { to: "/memory", label: "Memory", icon: Brain, end: false, adminOnly: false, color: "#22C55E" },
  { to: "/documents", label: "Documents", icon: FileText, end: false, adminOnly: false, color: "#F59E0B" },
  { to: "/workflows", label: "Workflows", icon: Workflow, end: false, adminOnly: false, color: "#06B6D4" },
  { to: "/tools", label: "Tools", icon: Wrench, end: false, adminOnly: false, color: "#F97316" },
  { to: "/admin", label: "Admin", icon: Shield, end: false, adminOnly: true, color: "#EF4444" },
];

interface NavTabsProps {
  onExpandChange?: (expanded: boolean) => void;
}

export function NavTabs({ onExpandChange }: NavTabsProps) {
  const location = useLocation();
  const isAdmin = useAuthStore((state) => state.user?.role === "admin");
  const [cmdOpen, setCmdOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const visibleTabs = TABS.filter((tab) => !tab.adminOnly || isAdmin);

  const toggleExpand = () => {
    const next = !expanded;
    setExpanded(next);
    onExpandChange?.(next);
  };

  return (
    <>
      <motion.aside
        animate={{ width: expanded ? 240 : 72 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="sidebar"
      >
        {/* Logo */}
        <div className="flex h-14 shrink-0 items-center px-4 border-b border-white/5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-brand font-display text-sm font-bold text-white shadow-glow-sm">
            V
          </div>
          <AnimatePresence>
            {expanded && (
              <motion.span
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                transition={{ duration: 0.2 }}
                className="ml-3 font-display text-sm font-bold text-white whitespace-nowrap"
              >
                Vikrm AI
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Search / Command Palette */}
        <div className="px-3 py-3 border-b border-white/5">
          <button
            onClick={() => setCmdOpen(true)}
            className={cn(
              "flex items-center gap-2.5 rounded-xl border border-border/60 bg-white/5 px-2.5 py-2 text-xs text-white/40 hover:border-primary/30 hover:text-white/70 transition-all duration-200 w-full",
            )}
            title="Command Palette (Ctrl+K)"
          >
            <Search className="h-3.5 w-3.5 shrink-0 text-accent" />
            <AnimatePresence>
              {expanded && (
                <motion.span
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -4 }}
                  transition={{ duration: 0.15 }}
                  className="flex items-center justify-between flex-1 whitespace-nowrap"
                >
                  <span>Search...</span>
                  <kbd className="rounded bg-white/10 px-1.5 font-mono text-[9px]">⌘K</kbd>
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 overflow-y-auto no-scrollbar px-3 py-3 space-y-0.5">
          {visibleTabs.map(({ to, label, icon: Icon, end, color }) => {
            const isActive =
              end ? location.pathname === to || location.pathname === "/" : location.pathname.startsWith(to);

            return (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive: linkActive }) =>
                  cn(
                    "sidebar-link group",
                    (linkActive || isActive) ? "active" : "",
                  )
                }
                title={!expanded ? label : undefined}
              >
                {({ isActive: linkActive }) => {
                  const active = linkActive || isActive;
                  return (
                    <>
                      {/* Active glow indicator */}
                      {active && (
                        <motion.div
                          layoutId="sidebarActiveGlow"
                          className="absolute inset-0 rounded-xl"
                          style={{
                            background: `radial-gradient(ellipse at 20% 50%, ${color}22 0%, transparent 70%)`,
                          }}
                          transition={{ type: "spring", stiffness: 400, damping: 35 }}
                        />
                      )}

                      <div className="relative z-10 flex items-center gap-3 w-full">
                        <div
                          className={cn(
                            "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-all duration-200",
                            active
                              ? "shadow-sm"
                              : "group-hover:scale-110",
                          )}
                          style={active ? {
                            background: `${color}25`,
                            boxShadow: `0 0 10px ${color}40`,
                          } : {}}
                        >
                          <Icon
                            className="h-4 w-4 transition-colors duration-200"
                            style={{ color: active ? color : undefined }}
                            strokeWidth={active ? 2 : 1.75}
                          />
                        </div>

                        <AnimatePresence>
                          {expanded && (
                            <motion.span
                              initial={{ opacity: 0, x: -8 }}
                              animate={{ opacity: 1, x: 0 }}
                              exit={{ opacity: 0, x: -8 }}
                              transition={{ duration: 0.2 }}
                              className="text-sm font-medium whitespace-nowrap"
                              style={{ color: active ? "white" : undefined }}
                            >
                              {label}
                            </motion.span>
                          )}
                        </AnimatePresence>
                      </div>
                    </>
                  );
                }}
              </NavLink>
            );
          })}
        </nav>

        {/* Divider */}
        <div className="px-3 py-1">
          <div className="h-px bg-white/5" />
        </div>

        {/* System Status indicator */}
        <div className="px-3 py-2">
          <div className={cn(
            "flex items-center gap-2.5 rounded-xl px-2.5 py-2",
            expanded ? "" : "justify-center",
          )}>
            <div className="relative flex h-2 w-2 shrink-0">
              <div className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
              <div className="relative inline-flex h-2 w-2 rounded-full bg-success" />
            </div>
            <AnimatePresence>
              {expanded && (
                <motion.span
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -4 }}
                  transition={{ duration: 0.15 }}
                  className="text-[11px] font-mono text-white/30 whitespace-nowrap"
                >
                  System Online
                </motion.span>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Spacer icon shortcut */}
        <div className="px-3 py-2">
          <div className={cn(
            "flex items-center gap-2.5 rounded-xl px-2.5 py-2",
            expanded ? "" : "justify-center",
          )}>
            <Zap className="h-3.5 w-3.5 shrink-0 text-warning/50" strokeWidth={1.5} />
            <AnimatePresence>
              {expanded && (
                <motion.span
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -4 }}
                  transition={{ duration: 0.15 }}
                  className="text-[11px] font-mono text-white/25 whitespace-nowrap"
                >
                  Vikrm Engine v1.0
                </motion.span>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* User Menu */}
        <div className="border-t border-white/5 px-3 py-3">
          <UserMenu collapsed={!expanded} />
        </div>

        {/* Collapse toggle */}
        <button
          onClick={toggleExpand}
          className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-surface text-white/50 hover:text-white hover:border-primary/40 transition-all duration-200 shadow-lg"
          title={expanded ? "Collapse sidebar" : "Expand sidebar"}
        >
          {expanded ? (
            <ChevronLeft className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
        </button>
      </motion.aside>

      <CommandPalette isOpen={cmdOpen} onClose={() => setCmdOpen(false)} />
    </>
  );
}
