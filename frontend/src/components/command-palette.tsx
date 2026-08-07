import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Brain,
  FileText,
  LayoutDashboard,
  MessageSquare,
  Search,
  Settings,
  Shield,
  Users,
  Workflow,
  Wrench,
  X,
  Sparkles,
  Clock,
} from "lucide-react";

import { useGlobalSearch } from "@/hooks/use-search";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const COMMANDS = [
  { id: "dashboard", label: "Go to Dashboard", path: "/dashboard", icon: LayoutDashboard, desc: "Overview and platform insights" },
  { id: "chat", label: "Start AI Chat", path: "/chat", icon: MessageSquare, desc: "Talk with your intelligent agents" },
  { id: "agents", label: "Agent Studio", path: "/agents", icon: Bot, desc: "Create and manage AI agents" },
  { id: "teams", label: "Agent Teams", path: "/teams", icon: Users, desc: "Orchestrate multi-agent workflows" },
  { id: "memory", label: "Memory Bank", path: "/memory", icon: Brain, desc: "Semantic knowledge and memory" },
  { id: "documents", label: "Document Vault", path: "/documents", icon: FileText, desc: "Manage uploaded documents and files" },
  { id: "workflows", label: "Workflow Builder", path: "/workflows", icon: Workflow, desc: "Visual automation pipelines" },
  { id: "tools", label: "Tools Registry", path: "/tools", icon: Wrench, desc: "Custom integrations and capabilities" },
  { id: "settings", label: "Settings", path: "/settings", icon: Settings, desc: "Profile, security, preferences" },
  { id: "admin", label: "Administration", path: "/admin", icon: Shield, desc: "System management and controls" },
];

const RECENT = ["dashboard", "chat", "agents"];

const CATEGORY_ICONS: Record<string, any> = {
  agent: Bot,
  chat: MessageSquare,
  document: FileText,
  memory: Brain,
  workflow: Workflow,
};

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  const { data: globalResults = [] } = useGlobalSearch(search);

  const filteredCommands = COMMANDS.filter((cmd) =>
    cmd.label.toLowerCase().includes(search.toLowerCase()) ||
    cmd.desc.toLowerCase().includes(search.toLowerCase()),
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) onClose();
        else setSearch("");
      } else if (e.key === "Escape" && isOpen) {
        onClose();
      } else if (e.key === "Enter" && isOpen) {
        e.preventDefault();
        if (globalResults.length > 0) {
          handleSelect(globalResults[0].path);
        } else if (filteredCommands.length > 0) {
          handleSelect(filteredCommands[0].path);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, search, filteredCommands, globalResults]);

  if (!isOpen) return null;

  const recentCommands = COMMANDS.filter((cmd) => RECENT.includes(cmd.id));
  const showRecent = search.length === 0;

  const handleSelect = (path: string) => {
    navigate(path);
    onClose();
    setSearch("");
  };

  return (
    <AnimatePresence>
      <div
        className="fixed inset-0 z-[100] flex items-start justify-center pt-24 px-4 backdrop-blur-md bg-black/60"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -10 }}
          transition={{ duration: 0.15 }}
          className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-primary/30 bg-surface/95 backdrop-blur-2xl shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Top glow */}
          <div
            className="absolute top-0 left-0 right-0 h-px"
            style={{ background: "linear-gradient(90deg, transparent, rgba(124,58,237,0.6), rgba(34,211,238,0.4), transparent)" }}
          />

          {/* Search input */}
          <div className="flex items-center gap-3 border-b border-border/80 px-4 py-3.5">
            <Search className="h-4 w-4 text-primary shrink-0" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search platform agents, chats, documents, workflows..."
              autoFocus
              className="w-full bg-transparent text-sm text-white placeholder:text-white/30 focus:outline-none"
            />
            {search && (
              <button onClick={() => setSearch("")} className="text-white/30 hover:text-white transition-colors">
                <X className="h-3.5 w-3.5" />
              </button>
            )}
            {!search && (
              <kbd className="rounded-lg border border-border bg-surface/60 px-2 py-0.5 font-mono text-[9px] text-white/30">Esc</kbd>
            )}
          </div>

          {/* Results Container */}
          <div className="max-h-80 overflow-y-auto no-scrollbar p-2">
            {showRecent && (
              <div className="mb-2">
                <div className="flex items-center gap-1.5 px-3 py-1.5 mb-1">
                  <Clock className="h-3 w-3 text-white/30" />
                  <span className="font-mono text-[10px] uppercase tracking-wider text-white/30">Recent Quick Access</span>
                </div>
                {recentCommands.map((cmd) => (
                  <button
                    key={cmd.id}
                    onClick={() => handleSelect(cmd.path)}
                    className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-xs text-white/70 hover:bg-white/8 hover:text-white transition-all group"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-surface/80 border border-border/60 group-hover:border-primary/30 transition-colors">
                      <cmd.icon className="h-3.5 w-3.5 text-primary/70 group-hover:text-primary transition-colors" />
                    </div>
                    <span className="font-medium">{cmd.label}</span>
                    <span className="ml-auto text-[10px] text-white/25">{cmd.desc}</span>
                  </button>
                ))}
                <div className="h-px bg-border/40 my-2 mx-3" />
              </div>
            )}

            {/* Live Search Results */}
            {globalResults.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center gap-1.5 px-3 py-1.5 mb-1">
                  <Sparkles className="h-3 w-3 text-accent" />
                  <span className="font-mono text-[10px] uppercase tracking-wider text-accent">Matching Items ({globalResults.length})</span>
                </div>
                {globalResults.map((item) => {
                  const Icon = CATEGORY_ICONS[item.category] || Sparkles;
                  return (
                    <button
                      key={`${item.category}-${item.id}`}
                      onClick={() => handleSelect(item.path)}
                      className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-xs text-white border border-accent/20 bg-accent/5 hover:bg-accent/15 transition-all group mb-1 text-left"
                    >
                      <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/20 border border-accent/30 shrink-0">
                        <Icon className="h-3.5 w-3.5 text-accent" />
                      </div>
                      <div className="flex flex-col min-w-0 flex-1">
                        <span className="font-bold truncate">{item.title}</span>
                        <span className="text-[10px] text-white/40 truncate">{item.description}</span>
                      </div>
                      <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-white/10 text-white/40">{item.category}</span>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Feature pages */}
            {filteredCommands.length > 0 && (
              <div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 mb-1">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-white/30">Platform Pages</span>
                </div>
                {filteredCommands.map((cmd) => (
                  <button
                    key={cmd.id}
                    onClick={() => handleSelect(cmd.path)}
                    className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-xs text-white/70 hover:bg-white/5 hover:text-white transition-all group text-left"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-surface/80 border border-border/60 group-hover:border-primary/30">
                      <cmd.icon className="h-3.5 w-3.5 text-primary/70 group-hover:text-primary" />
                    </div>
                    <div className="flex flex-col items-start min-w-0">
                      <span className="font-medium">{cmd.label}</span>
                      <span className="text-[10px] text-white/30 truncate">{cmd.desc}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer hint */}
          <div className="border-t border-border/40 px-4 py-2 flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-[10px] text-white/25">
              <kbd className="rounded border border-border px-1.5 py-0.5 font-mono text-[9px]">↵</kbd>
              <span>Open</span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-white/25">
              <kbd className="rounded border border-border px-1.5 py-0.5 font-mono text-[9px]">Esc</kbd>
              <span>Close</span>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
