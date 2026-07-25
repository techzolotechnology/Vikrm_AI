import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Plus, Search, Trash2, X, Loader2, Sparkles } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageTransition } from "@/components/page-transition";
import { useCreateMemory, useDeleteMemory, useMemories, useSearchMemories } from "@/hooks/use-memories";
import type { Memory } from "@/types/memory";

const TYPE_CONFIG: Record<Memory["memory_type"], { label: string; color: string; bg: string; border: string }> = {
  fact: {
    label: "Fact",
    color: "text-primary",
    bg: "bg-primary/15",
    border: "border-primary/30",
  },
  preference: {
    label: "Preference",
    color: "text-accent",
    bg: "bg-accent/15",
    border: "border-accent/30",
  },
  context: {
    label: "Context",
    color: "text-warning",
    bg: "bg-warning/15",
    border: "border-warning/30",
  },
};

export function MemoryViewer() {
  const { data: memories = [], isLoading } = useMemories();
  const createMemory = useCreateMemory();
  const deleteMemory = useDeleteMemory();
  const searchMemories = useSearchMemories();

  const [newContent, setNewContent] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<{ memory: Memory; distance: number }[] | null>(null);

  const handleAdd = () => {
    if (!newContent.trim()) return;
    createMemory.mutate({ content: newContent.trim() }, { onSuccess: () => setNewContent("") });
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    searchMemories.mutate(
      { query: searchQuery.trim(), top_k: 5 },
      { onSuccess: (data) => setSearchResults(data) },
    );
  };

  const displayedMemories = searchResults ? searchResults.map((r) => r.memory) : memories;

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        <div className="mx-auto max-w-4xl">
          {/* Page Header */}
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div
                className="page-icon-wrap"
                style={{ background: "linear-gradient(135deg, rgba(34,197,94,0.2) 0%, rgba(16,185,129,0.1) 100%)", borderColor: "rgba(34,197,94,0.3)" }}
              >
                <Brain className="h-5 w-5" style={{ color: "#22C55E" }} strokeWidth={1.75} />
              </div>
              <div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
                  Long-Term Storage
                </span>
                <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                  Memory Bank
                </h1>
                <p className="text-sm text-white/40">
                  Semantic facts and preferences remembered across all conversations.
                </p>
              </div>
            </div>
            {memories.length > 0 && (
              <span className="font-mono text-[11px] text-white/30">
                {memories.length} memor{memories.length !== 1 ? "ies" : "y"}
              </span>
            )}
          </div>

          {/* Add Memory */}
          <div className="mb-4 glass-card overflow-hidden border border-border/70 shadow-xl">
            <div className="p-1">
              <div className="flex gap-2 p-2">
                <div className="flex-1 relative">
                  <Sparkles className="pointer-events-none absolute left-3.5 top-3 h-3.5 w-3.5 text-accent/50" />
                  <input
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                    placeholder="Add a fact or preference (e.g. 'My team uses TypeScript')..."
                    className="input pl-9 text-sm bg-background/40 border-transparent focus:border-primary/30"
                  />
                </div>
                <motion.button
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.96 }}
                  onClick={handleAdd}
                  disabled={!newContent.trim() || createMemory.isPending}
                  className="flex shrink-0 items-center gap-2 rounded-xl bg-gradient-brand px-5 text-xs font-bold text-white shadow-glow-sm disabled:opacity-40 transition-all"
                >
                  {createMemory.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" strokeWidth={2} />
                  )}
                  Remember
                </motion.button>
              </div>
            </div>
          </div>

          {/* Search */}
          <div className="mb-6 flex gap-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Semantic memory search..."
                className="input pl-10 text-xs"
              />
            </div>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleSearch}
              className="btn-primary text-xs px-5"
            >
              {searchMemories.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Search"}
            </motion.button>
            {searchResults && (
              <motion.button
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                onClick={() => { setSearchResults(null); setSearchQuery(""); }}
                className="flex items-center gap-1.5 rounded-xl border border-border px-3 text-xs text-white/50 hover:text-white transition"
              >
                <X className="h-3.5 w-3.5" />
                Clear
              </motion.button>
            )}
          </div>

          {/* Search result label */}
          {searchResults && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-3 flex items-center gap-2"
            >
              <Search className="h-3.5 w-3.5 text-white/30" />
              <span className="font-mono text-[11px] text-white/40">
                {searchResults.length} result{searchResults.length !== 1 ? "s" : ""} for "{searchQuery}"
              </span>
            </motion.div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="space-y-2.5">
              {[1, 2, 3].map((i) => (
                <div key={i} className="glass-card h-14 skeleton" />
              ))}
            </div>
          )}

          {/* Empty */}
          {!isLoading && displayedMemories.length === 0 && (
            <EmptyState
              icon={Brain}
              title={searchResults ? "No matching memories" : "No memories saved yet"}
              description="Add facts above or chat with agents. Key preferences are saved to vector store automatically."
            />
          )}

          {/* Memory List */}
          <AnimatePresence initial={false}>
            <div className="space-y-2.5">
              {displayedMemories.map((memory, index) => {
                const cfg = TYPE_CONFIG[memory.memory_type] ?? TYPE_CONFIG.fact;
                return (
                  <motion.div
                    key={memory.id}
                    initial={{ opacity: 0, y: 10, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ delay: index * 0.03, duration: 0.25 }}
                    className="glass-card group flex items-start justify-between gap-4 p-4 border border-border/70 hover:border-white/15 transition-all duration-200"
                  >
                    <div className="flex items-start gap-3.5 min-w-0">
                      <span
                        className={`mt-0.5 shrink-0 rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-bold ${cfg.bg} ${cfg.border} ${cfg.color}`}
                      >
                        {cfg.label}
                      </span>
                      <p className="text-sm font-medium text-white/90 leading-relaxed">{memory.content}</p>
                    </div>
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => deleteMemory.mutate(memory.id)}
                      className="shrink-0 flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/20 hover:text-danger hover:border-danger/30 transition-all opacity-0 group-hover:opacity-100"
                      aria-label="Delete memory"
                    >
                      <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                    </motion.button>
                  </motion.div>
                );
              })}
            </div>
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  );
}
