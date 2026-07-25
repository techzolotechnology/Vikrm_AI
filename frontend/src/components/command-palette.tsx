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
  Shield,
  Users,
  Workflow,
  Wrench,
  X,
} from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const COMMANDS = [
  { id: "dashboard", label: "Go to Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { id: "chat", label: "Start AI Chat", path: "/chat", icon: MessageSquare },
  { id: "agents", label: "Manage Agents", path: "/agents", icon: Bot },
  { id: "teams", label: "Agent Orchestration Teams", path: "/teams", icon: Users },
  { id: "memory", label: "Memory Knowledge Bank", path: "/memory", icon: Brain },
  { id: "documents", label: "Document RAG Knowledge Base", path: "/documents", icon: FileText },
  { id: "workflows", label: "Workflow Builder", path: "/workflows", icon: Workflow },
  { id: "tools", label: "System Tools Registry", path: "/tools", icon: Wrench },
  { id: "admin", label: "Admin Panel & Telemetry", path: "/admin", icon: Shield },
];

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) onClose();
        else setSearch("");
      } else if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filtered = COMMANDS.filter((cmd) =>
    cmd.label.toLowerCase().includes(search.toLowerCase()),
  );

  const handleSelect = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <AnimatePresence>
      <div
        className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 backdrop-blur-md bg-black/60"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -10 }}
          transition={{ duration: 0.15 }}
          className="relative w-full max-w-lg glass-card overflow-hidden border border-primary/30 shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center gap-3 border-b border-border/80 px-4 py-3">
            <Search className="h-4 w-4 text-primary shrink-0" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search features, commands, or jump to page... (Esc to exit)"
              autoFocus
              className="w-full bg-transparent text-sm text-white placeholder:text-white/30 focus:outline-none"
            />
            <button onClick={onClose} className="text-white/30 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="max-h-72 overflow-y-auto p-2">
            {filtered.length === 0 ? (
              <p className="p-4 text-center text-xs text-white/30">No matching commands found.</p>
            ) : (
              filtered.map((cmd) => (
                <button
                  key={cmd.id}
                  onClick={() => handleSelect(cmd.path)}
                  className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-xs text-white/70 hover:bg-white/10 hover:text-white transition"
                >
                  <div className="flex items-center gap-3">
                    <cmd.icon className="h-4 w-4 text-primary" />
                    <span>{cmd.label}</span>
                  </div>
                  <span className="font-mono text-[10px] text-white/30">{cmd.path}</span>
                </button>
              ))
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
