import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, MessageSquare, MessageSquarePlus, Pin, Search, Trash2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Agent } from "@/types/agent";
import type { Conversation } from "@/types/chat";

interface ConversationSidebarProps {
  conversations: Conversation[];
  agents: Agent[];
  activeId: number | null;
  onSelect: (id: number) => void;
  onCreate: (agentId: number | null) => void;
  onDelete: (id: number) => void;
  isCreating: boolean;
}

export function ConversationSidebar({
  conversations,
  agents,
  activeId,
  onSelect,
  onCreate,
  onDelete,
  isCreating,
}: ConversationSidebarProps) {
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [filterText, setFilterText] = useState("");

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(filterText.toLowerCase()),
  );

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col gap-0 border-r border-border/60 bg-surface/30 backdrop-blur-xl">
      {/* Header */}
      <div className="px-4 pt-5 pb-3 border-b border-border/40">
        <h2 className="font-display text-xs font-semibold uppercase tracking-wider text-white/40 mb-3">
          Conversations
        </h2>

        {/* Agent selector */}
        {agents.length > 0 && (
          <div className="relative mb-3">
            <Bot className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-white/30" />
            <select
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="w-full rounded-xl border border-border/60 bg-surface/60 py-2 pl-8 pr-3 text-xs text-white/80 focus:border-primary/40 focus:outline-none appearance-none cursor-pointer"
            >
              <option value="">Default Assistant</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* New conversation button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onCreate(selectedAgentId ? Number(selectedAgentId) : null)}
          disabled={isCreating}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-brand px-4 py-2.5 text-xs font-bold text-white shadow-glow-sm transition-all disabled:opacity-50"
        >
          {isCreating ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="h-3.5 w-3.5 rounded-full border-2 border-white/40 border-t-white"
            />
          ) : (
            <MessageSquarePlus className="h-3.5 w-3.5" strokeWidth={2} />
          )}
          {isCreating ? "Creating..." : "New Chat"}
        </motion.button>
      </div>

      {/* Search */}
      <div className="px-4 py-3 border-b border-border/30">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-white/30" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Search threads..."
            className="w-full rounded-xl border border-border/40 bg-background/40 py-2 pl-8 pr-3 text-xs text-white placeholder:text-white/25 focus:border-primary/40 focus:outline-none transition-colors"
          />
        </div>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto no-scrollbar px-2 py-2">
        {conversations.length === 0 && (
          <div className="mt-8 px-4 text-center">
            <MessageSquare className="mx-auto h-8 w-8 text-white/15" />
            <p className="mt-3 text-xs text-white/35">No conversations yet.</p>
            <p className="mt-1 text-[11px] text-white/20">
              Start your first chat above.
            </p>
          </div>
        )}

        {filterText && filtered.length === 0 && conversations.length > 0 && (
          <p className="mt-4 text-center text-xs text-white/30">No results found.</p>
        )}

        <AnimatePresence initial={false}>
          {filtered.map((conversation, i) => {
            const isActive = conversation.id === activeId;
            return (
              <motion.div
                key={conversation.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                transition={{ delay: i * 0.02, duration: 0.2 }}
                onClick={() => onSelect(conversation.id)}
                className={cn(
                  "group relative flex cursor-pointer items-center justify-between rounded-xl px-3 py-2.5 text-xs font-medium transition-all duration-200 mb-0.5",
                  isActive
                    ? "bg-primary/15 text-white border border-primary/20 shadow-sm"
                    : "text-white/55 hover:bg-white/5 hover:text-white border border-transparent",
                )}
              >
                {/* Active indicator */}
                {isActive && (
                  <motion.div
                    layoutId="activeConversation"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 rounded-r-full bg-gradient-to-b from-primary to-accent"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}

                <div className="flex min-w-0 items-center gap-2 pl-1">
                  <MessageSquare
                    className={cn(
                      "h-3.5 w-3.5 shrink-0 transition-colors",
                      isActive ? "text-accent" : "text-white/25",
                    )}
                  />
                  <span className="truncate">{conversation.title}</span>
                </div>

                <div className="flex shrink-0 items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                    }}
                    className="rounded-md p-1 text-white/30 hover:text-white/60 transition-colors"
                    title="Pin conversation"
                  >
                    <Pin className="h-3 w-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(conversation.id);
                    }}
                    className="rounded-md p-1 text-white/30 hover:text-danger transition-colors"
                    aria-label="Delete conversation"
                    title="Delete"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="border-t border-border/30 px-4 py-3">
        <p className="font-mono text-[10px] text-white/20">
          {conversations.length} conversation{conversations.length !== 1 ? "s" : ""}
        </p>
      </div>
    </aside>
  );
}
