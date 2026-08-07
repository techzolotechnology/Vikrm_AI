import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Plus,
  Search,
  Trash2,
  X,
  Loader2,
  Sparkles,
  Pin,
  Edit2,
  Check,
  Calendar,

  AlertCircle,
} from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageTransition } from "@/components/page-transition";
import { Tooltip } from "@/components/ui/tooltip";
import { useCreateMemory, useDeleteMemory, useMemories, useSearchMemories, useUpdateMemory } from "@/hooks/use-memories";
import { cn } from "@/lib/utils";
import type { Memory } from "@/types/memory";

const TYPE_CONFIG: Record<Memory["memory_type"], { label: string; color: string; bg: string; border: string; dot: string }> = {
  fact: {
    label: "Fact",
    color: "text-primary",
    bg: "bg-primary/15",
    border: "border-primary/30",
    dot: "#7C3AED",
  },
  preference: {
    label: "Preference",
    color: "text-accent",
    bg: "bg-accent/15",
    border: "border-accent/30",
    dot: "#22D3EE",
  },
  context: {
    label: "Context",
    color: "text-warning",
    bg: "bg-warning/15",
    border: "border-warning/30",
    dot: "#F59E0B",
  },
};

const FILTER_TABS = [
  { id: "all", label: "All" },
  { id: "fact", label: "Facts" },
  { id: "preference", label: "Preferences" },
  { id: "context", label: "Context" },
];

// ─── Delete Confirmation Dialog ───────────────────────────────────────────────

interface DeleteDialogProps {
  onConfirm: () => void;
  onCancel: () => void;
}

function DeleteDialog({ onConfirm, onCancel }: DeleteDialogProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onCancel}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="glass-card w-full max-w-sm border border-danger/30 p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-danger/30 bg-danger/10">
            <AlertCircle className="h-5 w-5 text-danger" />
          </div>
          <div>
            <h3 className="font-display text-sm font-bold text-white">Delete Memory</h3>
            <p className="text-xs text-white/50">This action cannot be undone.</p>
          </div>
        </div>
        <p className="text-sm text-white/70 mb-6 leading-relaxed">
          Are you sure you want to permanently delete this memory? It will be removed from the vector store immediately.
        </p>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 rounded-xl border border-border/60 bg-surface/60 px-4 py-2 text-xs font-medium text-white/70 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 rounded-xl bg-danger/90 px-4 py-2 text-xs font-bold text-white hover:bg-danger transition-colors"
          >
            Delete Memory
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Group memories by time ───────────────────────────────────────────────────

function groupByTime(memories: Memory[]) {
  const now = Date.now();
  const today = now - 86400000;
  const week = now - 7 * 86400000;

  const pinned: Memory[] = [];
  const todayList: Memory[] = [];
  const weekList: Memory[] = [];
  const olderList: Memory[] = [];

  memories.forEach((m) => {
    if (m.is_pinned) { pinned.push(m); return; }
    const t = new Date(m.created_at || 0).getTime();
    if (t > today) todayList.push(m);
    else if (t > week) weekList.push(m);
    else olderList.push(m);
  });

  return { pinned, todayList, weekList, olderList };
}

// ─── Memory Item ──────────────────────────────────────────────────────────────

interface MemoryItemProps {
  memory: Memory;
  onPin: (m: Memory) => void;
  onEdit: (id: number, content: string) => void;
  onDelete: (id: number) => void;
  isDeleting?: boolean;
}

function MemoryItem({ memory, onPin, onEdit, onDelete, isDeleting }: MemoryItemProps) {
  const [editingContent, setEditingContent] = useState(memory.content);
  const [isEditing, setIsEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const cfg = TYPE_CONFIG[memory.memory_type] ?? TYPE_CONFIG.fact;

  const handleSaveEdit = () => {
    if (editingContent.trim()) {
      onEdit(memory.id, editingContent.trim());
      setIsEditing(false);
    }
  };

  return (
    <>
      <motion.div
        layout
        initial={{ opacity: 0, y: 10, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, x: -20, scale: 0.97 }}
        transition={{ duration: 0.25 }}
        className={cn(
          "glass-card group flex items-start justify-between gap-4 p-4 border transition-all duration-200",
          memory.is_pinned
            ? "border-warning/40 bg-warning/5"
            : "border-border/70 hover:border-white/15",
        )}
      >
        <div className="flex items-start gap-3.5 min-w-0 flex-1">
          {/* Type badge */}
          <span
            className={`mt-0.5 shrink-0 rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-bold ${cfg.bg} ${cfg.border} ${cfg.color}`}
          >
            {cfg.label}
          </span>

          {/* Content */}
          {isEditing ? (
            <div className="flex-1 flex gap-2">
              <input
                value={editingContent}
                onChange={(e) => setEditingContent(e.target.value)}
                className="input text-xs py-1 px-2 flex-1"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSaveEdit();
                  if (e.key === "Escape") setIsEditing(false);
                }}
              />
              <button onClick={handleSaveEdit} className="text-success p-1 hover:scale-110 transition-transform">
                <Check className="h-4 w-4" />
              </button>
              <button onClick={() => setIsEditing(false)} className="text-white/40 hover:text-white p-1">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <p className="text-sm font-medium text-white/90 leading-relaxed flex-1">{memory.content}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0">
          {/* Importance score */}
          {(memory as any).importance_score !== undefined && (
            <Tooltip content={`Importance: ${((memory as any).importance_score * 100).toFixed(0)}%`} side="top">
              <div className="h-1.5 w-10 rounded-full bg-white/10 overflow-hidden mr-1">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
                  style={{ width: `${((memory as any).importance_score ?? 0) * 100}%` }}
                />
              </div>
            </Tooltip>
          )}

          <Tooltip content={memory.is_pinned ? "Unpin" : "Pin memory"} side="top">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => onPin(memory)}
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 transition-all",
                memory.is_pinned
                  ? "text-warning border-warning/40"
                  : "text-white/20 hover:text-warning opacity-0 group-hover:opacity-100",
              )}
            >
              <Pin className="h-3.5 w-3.5" />
            </motion.button>
          </Tooltip>

          <Tooltip content="Edit memory" side="top">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => { setIsEditing(true); setEditingContent(memory.content); }}
              className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/20 hover:text-white transition-all opacity-0 group-hover:opacity-100"
            >
              <Edit2 className="h-3.5 w-3.5" />
            </motion.button>
          </Tooltip>

          <Tooltip content="Delete memory" side="top">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setConfirmDelete(true)}
              disabled={isDeleting}
              className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/20 hover:text-danger hover:border-danger/30 transition-all opacity-0 group-hover:opacity-100"
            >
              {isDeleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />}
            </motion.button>
          </Tooltip>
        </div>
      </motion.div>

      <AnimatePresence>
        {confirmDelete && (
          <DeleteDialog
            onConfirm={() => { onDelete(memory.id); setConfirmDelete(false); }}
            onCancel={() => setConfirmDelete(false)}
          />
        )}
      </AnimatePresence>
    </>
  );
}

// ─── Group header ─────────────────────────────────────────────────────────────

function GroupHeader({ label, count }: { label: string; count: number }) {
  return (
    <div className="flex items-center gap-2 mb-2 mt-4 first:mt-0">
      <Calendar className="h-3.5 w-3.5 text-white/25" />
      <span className="font-mono text-[11px] uppercase tracking-wider text-white/30">{label}</span>
      <span className="font-mono text-[10px] text-white/20">({count})</span>
      <div className="flex-1 h-px bg-border/30" />
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function MemoryViewer() {
  const [activeTab, setActiveTab] = useState("all");
  const { data: memories = [], isLoading } = useMemories(activeTab === "all" ? undefined : activeTab);
  const createMemory = useCreateMemory();
  const deleteMemory = useDeleteMemory();
  const updateMemory = useUpdateMemory();
  const searchMemories = useSearchMemories();

  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState<"fact" | "preference" | "context">("fact");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<{ memory: Memory; distance: number }[] | null>(null);

  const handleAdd = () => {
    if (!newContent.trim()) return;
    createMemory.mutate(
      { content: newContent.trim(), memory_type: newType },
      { onSuccess: () => setNewContent("") },
    );
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) { setSearchResults(null); return; }
    searchMemories.mutate(
      { query: searchQuery.trim(), top_k: 5 },
      { onSuccess: (data) => setSearchResults(data) },
    );
  };

  const handleTogglePin = (memory: Memory) => {
    updateMemory.mutate({ memoryId: memory.id, is_pinned: !memory.is_pinned });
  };

  const handleSaveEdit = (memoryId: number, content: string) => {
    updateMemory.mutate({ memoryId, content });
  };

  const displayedMemories = searchResults ? searchResults.map((r) => r.memory) : memories;
  const { pinned, todayList, weekList, olderList } = groupByTime(displayedMemories);

  // Counts per type for filter tabs
  const typeCounts = memories.reduce<Record<string, number>>((acc, m) => {
    acc[m.memory_type] = (acc[m.memory_type] || 0) + 1;
    return acc;
  }, {});

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        <div className="mx-auto max-w-4xl">
          {/* Page Header */}
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div
                className="page-icon-wrap"
                style={{
                  background: "linear-gradient(135deg, rgba(34,197,94,0.2) 0%, rgba(16,185,129,0.1) 100%)",
                  borderColor: "rgba(34,197,94,0.3)",
                }}
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
          <div className="mb-5 glass-card overflow-hidden border border-border/70 shadow-xl">
            <div className="p-3">
              <div className="flex flex-col sm:flex-row gap-2">
                <div className="flex-1 relative">
                  <Sparkles className="pointer-events-none absolute left-3.5 top-3 h-3.5 w-3.5 text-accent/50" />
                  <input
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                    placeholder="Add a fact or preference (e.g. 'My team uses TypeScript')..."
                    className="input pl-9 text-sm bg-background/40 border-transparent focus:border-primary/30 w-full"
                  />
                </div>
                <div className="flex gap-2">
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value as any)}
                    className="bg-surface/80 text-xs text-white border border-border/60 rounded-xl px-3 py-2 focus:outline-none cursor-pointer"
                  >
                    <option value="fact">Fact</option>
                    <option value="preference">Preference</option>
                    <option value="context">Context</option>
                  </select>
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
          </div>

          {/* Filter Tabs + Search */}
          <div className="mb-6 flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="flex items-center gap-1 bg-surface/40 border border-border/60 p-1 rounded-xl w-full sm:w-auto">
              {FILTER_TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); setSearchResults(null); }}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all",
                    activeTab === tab.id
                      ? "bg-primary/20 text-accent border border-primary/30"
                      : "text-white/40 hover:text-white",
                  )}
                >
                  {tab.label}
                  {tab.id !== "all" && typeCounts[tab.id] > 0 && (
                    <span className={cn(
                      "rounded-full px-1.5 py-0.5 font-mono text-[9px]",
                      activeTab === tab.id ? "bg-primary/30 text-accent" : "bg-white/10 text-white/30",
                    )}>
                      {typeCounts[tab.id]}
                    </span>
                  )}
                  {tab.id === "all" && (
                    <span className={cn(
                      "rounded-full px-1.5 py-0.5 font-mono text-[9px]",
                      activeTab === tab.id ? "bg-primary/30 text-accent" : "bg-white/10 text-white/30",
                    )}>
                      {memories.length}
                    </span>
                  )}
                </button>
              ))}
            </div>

            <div className="flex gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-64">
                <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="Semantic memory search..."
                  className="input pl-10 text-xs w-full"
                />
              </div>
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleSearch}
                className="btn-primary text-xs px-4"
              >
                {searchMemories.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Search"}
              </motion.button>
              {searchResults && (
                <motion.button
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  onClick={() => { setSearchResults(null); setSearchQuery(""); }}
                  className="flex items-center gap-1 rounded-xl border border-border/60 px-3 text-xs text-white/50 hover:text-white transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
                  Clear
                </motion.button>
              )}
            </div>
          </div>

          {/* Search result banner */}
          {searchResults && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 px-4 py-2.5 text-xs"
            >
              <Search className="h-3.5 w-3.5 text-accent" />
              <span className="text-white/60">
                Found <span className="text-white font-bold">{searchResults.length}</span> semantically similar{" "}
                memor{searchResults.length !== 1 ? "ies" : "y"} for "{searchQuery}"
              </span>
            </motion.div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="space-y-2.5">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="glass-card h-14 skeleton" />
              ))}
            </div>
          )}

          {/* Empty */}
          {!isLoading && displayedMemories.length === 0 && (
            <EmptyState
              icon={Brain}
              title={searchResults ? "No matching memories" : "No memories saved yet"}
              description="Add facts above or chat with agents. Key preferences are automatically saved to the vector store."
            />
          )}

          {/* Memory list grouped by time */}
          {!isLoading && displayedMemories.length > 0 && (
            <AnimatePresence initial={false}>
              <div>
                {/* Pinned */}
                {pinned.length > 0 && !searchResults && (
                  <>
                    <GroupHeader label="📌 Pinned" count={pinned.length} />
                    <div className="space-y-2 mb-2">
                      {pinned.map((m) => (
                        <MemoryItem
                          key={m.id}
                          memory={m}
                          onPin={handleTogglePin}
                          onEdit={handleSaveEdit}
                          onDelete={(id) => deleteMemory.mutate(id)}
                        />
                      ))}
                    </div>
                  </>
                )}

                {/* Today */}
                {todayList.length > 0 && !searchResults && (
                  <>
                    <GroupHeader label="Today" count={todayList.length} />
                    <div className="space-y-2 mb-2">
                      {todayList.map((m) => (
                        <MemoryItem key={m.id} memory={m} onPin={handleTogglePin} onEdit={handleSaveEdit} onDelete={(id) => deleteMemory.mutate(id)} />
                      ))}
                    </div>
                  </>
                )}

                {/* This week */}
                {weekList.length > 0 && !searchResults && (
                  <>
                    <GroupHeader label="This Week" count={weekList.length} />
                    <div className="space-y-2 mb-2">
                      {weekList.map((m) => (
                        <MemoryItem key={m.id} memory={m} onPin={handleTogglePin} onEdit={handleSaveEdit} onDelete={(id) => deleteMemory.mutate(id)} />
                      ))}
                    </div>
                  </>
                )}

                {/* Older */}
                {olderList.length > 0 && !searchResults && (
                  <>
                    <GroupHeader label="Older" count={olderList.length} />
                    <div className="space-y-2 mb-2">
                      {olderList.map((m) => (
                        <MemoryItem key={m.id} memory={m} onPin={handleTogglePin} onEdit={handleSaveEdit} onDelete={(id) => deleteMemory.mutate(id)} />
                      ))}
                    </div>
                  </>
                )}

                {/* Search results (flat) */}
                {searchResults && (
                  <div className="space-y-2.5">
                    {displayedMemories.map((m) => (
                      <MemoryItem key={m.id} memory={m} onPin={handleTogglePin} onEdit={handleSaveEdit} onDelete={(id) => deleteMemory.mutate(id)} />
                    ))}
                  </div>
                )}
              </div>
            </AnimatePresence>
          )}
        </div>
      </div>
    </PageTransition>
  );
}
