import { useState, type DragEvent, type ElementType } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  ChevronDown,
  ChevronRight,
  GitBranch,
  LogOut,
  MessageSquare,
  Search,
  Sparkles,
  Wrench,
} from "lucide-react";

import type { WorkflowNodeType } from "@/types/workflow";

interface PaletteItem {
  type: WorkflowNodeType;
  label: string;
  description: string;
  icon: ElementType;
  color: string;
}

interface Category {
  id: string;
  label: string;
  icon: ElementType;
  items: PaletteItem[];
}

const CATEGORIES: Category[] = [
  {
    id: "ai",
    label: "⭐ AI & Agents",
    icon: Sparkles,
    items: [
      { type: "agent", label: "Autonomous Agent", description: "Multi-step reasoning agent", icon: Bot, color: "#22D3EE" },
      { type: "llm", label: "LLM Completion", description: "Direct prompt model execution", icon: MessageSquare, color: "#7C3AED" },
    ],
  },
  {
    id: "logic",
    label: "⚙ Logic & Control",
    icon: GitBranch,
    items: [
      { type: "condition", label: "Logic Branch", description: "If/Else conditional route", icon: GitBranch, color: "#F59E0B" },
    ],
  },
  {
    id: "tools",
    label: "🔧 Tools & Actions",
    icon: Wrench,
    items: [
      { type: "tool", label: "System Tool", description: "Python, Calculator, HTTP request", icon: Wrench, color: "#F59E0B" },
    ],
  },
  {
    id: "output",
    label: "📄 Output & Results",
    icon: LogOut,
    items: [
      { type: "output", label: "Output Synthesizer", description: "Format and return final response", icon: LogOut, color: "#EC4899" },
    ],
  },
];

export function NodePalette() {
  const [search, setSearch] = useState("");
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const handleDragStart = (event: DragEvent, nodeType: WorkflowNodeType) => {
    event.dataTransfer.setData("application/vikrm-node-type", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  const toggleCategory = (id: string) => {
    setCollapsed((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <aside className="glass-card-elevated absolute left-4 top-20 z-20 flex w-64 flex-col gap-3 p-4 shadow-2xl backdrop-blur-2xl max-h-[calc(100vh-120px)] overflow-y-auto no-scrollbar border border-border/80">
      <div className="flex items-center justify-between">
        <span className="font-display text-xs font-bold uppercase tracking-wider text-white/50 flex items-center gap-1.5">
          <Sparkles className="h-3.5 w-3.5 text-accent" /> Node Library
        </span>
        <span className="font-mono text-[10px] text-white/30">Drag to canvas</span>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-white/30" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search nodes..."
          className="w-full rounded-xl border border-border/60 bg-background/50 pl-8 pr-3 py-1.5 text-xs text-white placeholder:text-white/35 focus:border-primary/40 focus:outline-none"
        />
      </div>

      <div className="space-y-3 pt-1">
        {CATEGORIES.map((cat) => {
          const isCollapsed = collapsed[cat.id];
          const filteredItems = cat.items.filter(
            (item) =>
              item.label.toLowerCase().includes(search.toLowerCase()) ||
              item.description.toLowerCase().includes(search.toLowerCase()),
          );

          if (search && filteredItems.length === 0) return null;

          return (
            <div key={cat.id} className="space-y-1.5">
              <button
                onClick={() => toggleCategory(cat.id)}
                className="flex w-full items-center justify-between text-left text-xs font-semibold text-white/70 hover:text-white transition"
              >
                <span>{cat.label}</span>
                {isCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>

              <AnimatePresence initial={false}>
                {!isCollapsed && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="space-y-1.5 overflow-hidden"
                  >
                    {filteredItems.map(({ type, label, description, icon: Icon, color }) => (
                      <motion.div
                        key={type}
                        draggable
                        whileHover={{ x: 3, scale: 1.01 }}
                        onDragStart={(e) => handleDragStart(e as unknown as DragEvent, type)}
                        className="group flex cursor-grab items-start gap-2.5 rounded-xl border border-border/60 bg-surface/50 p-2.5 text-xs transition-all hover:border-primary/40 hover:bg-surface/90 hover:shadow-glow-sm active:cursor-grabbing"
                      >
                        <div
                          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border transition-transform group-hover:scale-110"
                          style={{ backgroundColor: `${color}20`, borderColor: `${color}40` }}
                        >
                          <Icon className="h-3.5 w-3.5" style={{ color }} strokeWidth={2} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="font-semibold text-white group-hover:text-primary-hover transition-colors">
                            {label}
                          </p>
                          <p className="text-[10px] text-white/40 leading-tight truncate">{description}</p>
                        </div>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
