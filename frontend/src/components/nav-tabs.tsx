import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Brain,
  ChevronLeft,
  ChevronRight,
  Code2,
  FileText,
  LayoutDashboard,
  MessageSquare,
  Search,
  Settings,
  Shield,
  Users,
  Workflow,
  Wrench,
} from "lucide-react";

import { CommandPalette } from "@/components/command-palette";
import { Tooltip } from "@/components/ui/tooltip";
import { UserMenu } from "@/components/user-menu";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/use-auth-store";

const TABS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true, adminOnly: false, color: "#7C3AED", shortcut: "G then D" },
  { to: "/workspace", label: "Code Workspace", icon: Code2, end: false, adminOnly: false, color: "#3B82F6", shortcut: "G then O" },
  { to: "/chat", label: "Chat", icon: MessageSquare, end: false, adminOnly: false, color: "#22D3EE", shortcut: "G then C" },
  { to: "/agents", label: "Agent Studio", icon: Bot, end: false, adminOnly: false, color: "#8B5CF6", shortcut: "G then A" },
  { to: "/teams", label: "Teams", icon: Users, end: false, adminOnly: false, color: "#EC4899", shortcut: "G then T" },
  { to: "/memory", label: "Memory", icon: Brain, end: false, adminOnly: false, color: "#22C55E", shortcut: "G then M" },
  { to: "/documents", label: "Documents", icon: FileText, end: false, adminOnly: false, color: "#F59E0B", shortcut: "G then K" },
  { to: "/workflows", label: "Workflows", icon: Workflow, end: false, adminOnly: false, color: "#06B6D4", shortcut: "G then W" },
  { to: "/tools", label: "Tools", icon: Wrench, end: false, adminOnly: false, color: "#F97316", shortcut: "G then L" },
];


const BOTTOM_TABS = [
  { to: "/settings", label: "Settings", icon: Settings, end: false, adminOnly: false, color: "#64748B", shortcut: "G then S" },
  { to: "/admin", label: "Admin", icon: Shield, end: false, adminOnly: true, color: "#EF4444", shortcut: "" },
];

// Keyboard nav shortcuts map: g → then key
const NAV_SHORTCUTS: Record<string, string> = {
  d: "/dashboard",
  o: "/workspace",
  c: "/chat",
  a: "/agents",
  t: "/teams",
  m: "/memory",
  k: "/documents",
  w: "/workflows",
  l: "/tools",
  s: "/settings",
};

interface NavTabsProps {
  onExpandChange?: (expanded: boolean) => void;
}

export function NavTabs({ onExpandChange }: NavTabsProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const isAdmin = useAuthStore((state) => state.user?.role === "admin");
  const [cmdOpen, setCmdOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [gPressed, setGPressed] = useState(false);

  const visibleTabs = TABS.filter((tab) => !tab.adminOnly || isAdmin);
  const visibleBottomTabs = BOTTOM_TABS.filter((tab) => !tab.adminOnly || isAdmin);

  const toggleExpand = () => {
    const next = !expanded;
    setExpanded(next);
    onExpandChange?.(next);
  };

  // Keyboard shortcuts
  useEffect(() => {
    let gTimer: ReturnType<typeof setTimeout>;

    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput = target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable;

      // Ctrl+K / Cmd+K → command palette
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setCmdOpen(true);
        return;
      }

      if (isInput) return;

      // G-chord navigation
      if (e.key === "g" && !e.ctrlKey && !e.metaKey) {
        setGPressed(true);
        if (gTimer) clearTimeout(gTimer);
        gTimer = setTimeout(() => setGPressed(false), 1500);
        return;
      }

      if (gPressed && NAV_SHORTCUTS[e.key.toLowerCase()]) {
        e.preventDefault();
        navigate(NAV_SHORTCUTS[e.key.toLowerCase()]);
        setGPressed(false);
        if (gTimer) clearTimeout(gTimer);
      }
    };

    document.addEventListener("keydown", handler);
    return () => {
      document.removeEventListener("keydown", handler);
      if (gTimer) clearTimeout(gTimer);
    };
  }, [gPressed, navigate]);

  const renderNavItem = ({
    to,
    label,
    icon: Icon,
    end,
    color,
    shortcut,
  }: typeof TABS[0]) => {
    const isActive = end
      ? location.pathname === to || location.pathname === "/"
      : location.pathname.startsWith(to);

    const tooltipContent = expanded ? "" : `${label}${shortcut ? ` (${shortcut})` : ""}`;

    return (
      <Tooltip key={to} content={tooltipContent} side="right" delay={300}>
        <NavLink
          to={to}
          end={end}
          className={cn("sidebar-link group w-full", isActive ? "active" : "")}
          aria-label={label}
        >
          {() => (
            <>
              {/* Active glow */}
              {isActive && (
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
                    isActive ? "shadow-sm" : "group-hover:scale-110",
                  )}
                  style={
                    isActive
                      ? { background: `${color}25`, boxShadow: `0 0 10px ${color}40` }
                      : {}
                  }
                >
                  <Icon
                    className="h-4 w-4 transition-colors duration-200"
                    style={{ color: isActive ? color : undefined }}
                    strokeWidth={isActive ? 2 : 1.75}
                  />
                </div>

                <AnimatePresence>
                  {expanded && (
                    <motion.div
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -8 }}
                      transition={{ duration: 0.2 }}
                      className="flex items-center justify-between flex-1 min-w-0"
                    >
                      <span
                        className="text-sm font-medium whitespace-nowrap"
                        style={{ color: isActive ? "white" : undefined }}
                      >
                        {label}
                      </span>
                      {shortcut && (
                        <span className="font-mono text-[9px] text-white/20 ml-2">
                          {shortcut.replace("G then ", "g+")}
                        </span>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </>
          )}
        </NavLink>
      </Tooltip>
    );
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
          <motion.div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-brand font-display text-sm font-bold text-white shadow-glow-sm cursor-pointer"
            whileHover={{ scale: 1.08, rotate: 3 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate("/dashboard")}
            title="Vikrm AI"
          >
            V
          </motion.div>
          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                transition={{ duration: 0.2 }}
                className="ml-3 whitespace-nowrap"
              >
                <div className="font-display text-sm font-bold text-white leading-tight">Vikrm AI</div>
                <div className="font-mono text-[9px] text-white/30 uppercase tracking-wider">Intelligence Platform</div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Search / Command Palette */}
        <div className="px-3 py-3 border-b border-white/5">
          <Tooltip content={expanded ? "" : "Search (Ctrl+K)"} side="right" delay={300}>
            <button
              onClick={() => setCmdOpen(true)}
              className="flex items-center gap-2.5 rounded-xl border border-border/60 bg-white/5 px-2.5 py-2 text-xs text-white/40 hover:border-primary/30 hover:text-white/70 transition-all duration-200 w-full"
              aria-label="Open command palette"
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
          </Tooltip>
        </div>

        {/* G-chord hint */}
        <AnimatePresence>
          {gPressed && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mx-3 mt-2 rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center"
            >
              <p className="font-mono text-[10px] text-accent">Press a key to navigate...</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Nav Links */}
        <nav className="flex-1 overflow-y-auto no-scrollbar px-3 py-3 space-y-0.5">
          {visibleTabs.map(renderNavItem)}
        </nav>

        {/* Divider */}
        <div className="px-3 py-1">
          <div className="h-px bg-white/5" />
        </div>

        {/* Bottom Nav */}
        <nav className="px-3 py-2 space-y-0.5">
          {visibleBottomTabs.map(renderNavItem)}
        </nav>

        {/* Platform Status */}
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
                  Platform Active
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
        <Tooltip content={expanded ? "Collapse sidebar" : "Expand sidebar"} side="right" delay={200}>
          <button
            onClick={toggleExpand}
            className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-surface text-white/50 hover:text-white hover:border-primary/40 transition-all duration-200 shadow-lg"
            aria-label={expanded ? "Collapse sidebar" : "Expand sidebar"}
          >
            {expanded ? (
              <ChevronLeft className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </button>
        </Tooltip>
      </motion.aside>

      <CommandPalette isOpen={cmdOpen} onClose={() => setCmdOpen(false)} />
    </>
  );
}
