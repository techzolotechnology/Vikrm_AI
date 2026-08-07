import { useState } from "react";
import { motion } from "framer-motion";
import {
  Bot,
  Copy,
  MessageSquare,
  MessageSquarePlus,
  MoreVertical,
  Pin,
  PinOff,
  Search,
  Trash2,
  Edit2,
  Archive,
  Check,
  X,
  Settings,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useUpdateConversation, useDuplicateConversation } from "@/hooks/use-chat";
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

// ─── Grouping Helper ───

function categorizeConversations(conversations: Conversation[]) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterday = today - 86400000;
  const lastWeek = today - 7 * 86400000;

  const pinned: Conversation[] = [];
  const todayList: Conversation[] = [];
  const yesterdayList: Conversation[] = [];
  const lastWeekList: Conversation[] = [];
  const olderList: Conversation[] = [];

  conversations.forEach((c) => {
    if (c.is_pinned) {
      pinned.push(c);
      return;
    }
    const updated = new Date(c.updated_at).getTime();
    if (updated >= today) {
      todayList.push(c);
    } else if (updated >= yesterday) {
      yesterdayList.push(c);
    } else if (updated >= lastWeek) {
      lastWeekList.push(c);
    } else {
      olderList.push(c);
    }
  });

  return { pinned, todayList, yesterdayList, lastWeekList, olderList };
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
  const navigate = useNavigate();
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [filterText, setFilterText] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [activeMenuId, setActiveMenuId] = useState<number | null>(null);

  const updateConversation = useUpdateConversation();
  const duplicateConversation = useDuplicateConversation();

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(filterText.toLowerCase()),
  );

  const { pinned, todayList, yesterdayList, lastWeekList, olderList } =
    categorizeConversations(filtered);

  const handleRenameSubmit = (id: number) => {
    if (!editTitle.trim()) {
      setEditingId(null);
      return;
    }
    updateConversation.mutate(
      { id, title: editTitle.trim() },
      { onSuccess: () => setEditingId(null) },
    );
  };

  const renderItem = (conversation: Conversation) => {
    const isActive = conversation.id === activeId;
    const isEditing = editingId === conversation.id;

    return (
      <motion.div
        key={conversation.id}
        initial={{ opacity: 0, x: -8 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -8 }}
        onClick={() => !isEditing && onSelect(conversation.id)}
        className={cn(
          "group relative flex cursor-pointer flex-col gap-1 rounded-xl px-3 py-2.5 text-xs transition-all duration-200 mb-1 border",
          isActive
            ? "bg-primary/15 text-white border-primary/30 shadow-sm"
            : "text-white/70 hover:bg-white/5 hover:text-white border-transparent",
        )}
      >
        {/* Active indicator bar */}
        {isActive && (
          <motion.div
            layoutId="activeSideBarGlow"
            className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-7 rounded-r-full bg-gradient-to-b from-primary to-accent"
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
          />
        )}

        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 flex-1 items-center gap-2">
            <MessageSquare
              className={cn(
                "h-3.5 w-3.5 shrink-0 transition-colors",
                isActive ? "text-accent" : "text-white/30",
              )}
            />
            {isEditing ? (
              <div className="flex items-center gap-1 flex-1" onClick={(e) => e.stopPropagation()}>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleRenameSubmit(conversation.id)}
                  autoFocus
                  className="w-full bg-background/80 px-2 py-1 rounded text-xs text-white border border-primary/50 focus:outline-none"
                />
                <button
                  onClick={() => handleRenameSubmit(conversation.id)}
                  className="text-success hover:scale-110"
                >
                  <Check className="h-3.5 w-3.5" />
                </button>
                <button onClick={() => setEditingId(null)} className="text-white/40 hover:text-white">
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <span className="truncate font-semibold text-white/90 group-hover:text-white">
                {conversation.title}
              </span>
            )}
          </div>

          {/* Hover Menu */}
          {!isEditing && (
            <div className="relative shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveMenuId(activeMenuId === conversation.id ? null : conversation.id);
                }}
                className="rounded-lg p-1 text-white/40 hover:text-white hover:bg-white/10"
              >
                <MoreVertical className="h-3.5 w-3.5" />
              </button>

              {/* Action Dropdown Menu */}
              {activeMenuId === conversation.id && (
                <div
                  className="absolute right-0 top-full mt-1 z-50 w-44 rounded-2xl border border-border/80 bg-surface/95 p-1.5 backdrop-blur-2xl shadow-2xl space-y-0.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => {
                      updateConversation.mutate({
                        id: conversation.id,
                        is_pinned: !conversation.is_pinned,
                      });
                      setActiveMenuId(null);
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs text-white/70 hover:bg-white/10 hover:text-white"
                  >
                    {conversation.is_pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
                    {conversation.is_pinned ? "Unpin" : "Pin Thread"}
                  </button>

                  <button
                    onClick={() => {
                      setEditingId(conversation.id);
                      setEditTitle(conversation.title);
                      setActiveMenuId(null);
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs text-white/70 hover:bg-white/10 hover:text-white"
                  >
                    <Edit2 className="h-3.5 w-3.5" />
                    Rename
                  </button>

                  <button
                    onClick={() => {
                      duplicateConversation.mutate(conversation.id);
                      setActiveMenuId(null);
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs text-white/70 hover:bg-white/10 hover:text-white"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    Duplicate
                  </button>

                  <button
                    onClick={() => {
                      updateConversation.mutate({
                        id: conversation.id,
                        is_archived: !conversation.is_archived,
                      });
                      setActiveMenuId(null);
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs text-white/70 hover:bg-white/10 hover:text-white"
                  >
                    <Archive className="h-3.5 w-3.5" />
                    {conversation.is_archived ? "Unarchive" : "Archive"}
                  </button>

                  <div className="h-px bg-border/40 my-1" />

                  <button
                    onClick={() => {
                      onDelete(conversation.id);
                      setActiveMenuId(null);
                    }}
                    className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs text-danger hover:bg-danger/10"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Date / Model details */}
        <div className="flex items-center justify-between text-[10px] text-white/30 font-mono pl-5">
          <span>{conversation.model}</span>
          <span>{new Date(conversation.updated_at).toLocaleDateString([], { month: "short", day: "numeric" })}</span>
        </div>
      </motion.div>
    );
  };

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col gap-0 border-r border-border/60 bg-surface/30 backdrop-blur-xl">
      {/* Header */}
      <div className="px-4 pt-5 pb-3 border-b border-border/40">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-xs font-semibold uppercase tracking-wider text-white/40">
            Conversations
          </h2>
        </div>

        {/* Agent Selector */}
        {agents.length > 0 && (
          <div className="relative mb-3">
            <Bot className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-white/30" />
            <select
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="w-full rounded-xl border border-border/60 bg-surface/60 py-2 pl-8 pr-3 text-xs text-white/80 focus:border-primary/40 focus:outline-none appearance-none cursor-pointer"
            >
              <option value="">Default AI Assistant</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* New Chat Button */}
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

      {/* Search Bar */}
      <div className="px-4 py-3 border-b border-border/30">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-white/30" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Search conversations..."
            className="w-full rounded-xl border border-border/40 bg-background/40 py-2 pl-8 pr-3 text-xs text-white placeholder:text-white/25 focus:border-primary/40 focus:outline-none transition-colors"
          />
        </div>
      </div>

      {/* Main Conversation List grouped by section */}
      <div className="flex-1 overflow-y-auto no-scrollbar px-2 py-2">
        {conversations.length === 0 && (
          <div className="mt-8 px-4 text-center">
            <MessageSquare className="mx-auto h-8 w-8 text-white/15" />
            <p className="mt-3 text-xs text-white/35">No conversations yet.</p>
            <p className="mt-1 text-[11px] text-white/20">Click New Chat above to start.</p>
          </div>
        )}

        {/* Pinned Section */}
        {pinned.length > 0 && (
          <div className="mb-3">
            <div className="flex items-center gap-1.5 px-2 mb-1.5 font-mono text-[10px] uppercase tracking-wider text-accent font-semibold">
              <Pin className="h-3 w-3" /> Pinned
            </div>
            {pinned.map(renderItem)}
          </div>
        )}

        {/* Today */}
        {todayList.length > 0 && (
          <div className="mb-3">
            <div className="px-2 mb-1.5 font-mono text-[10px] uppercase tracking-wider text-white/30">
              Today
            </div>
            {todayList.map(renderItem)}
          </div>
        )}

        {/* Yesterday */}
        {yesterdayList.length > 0 && (
          <div className="mb-3">
            <div className="px-2 mb-1.5 font-mono text-[10px] uppercase tracking-wider text-white/30">
              Yesterday
            </div>
            {yesterdayList.map(renderItem)}
          </div>
        )}

        {/* Previous 7 Days */}
        {lastWeekList.length > 0 && (
          <div className="mb-3">
            <div className="px-2 mb-1.5 font-mono text-[10px] uppercase tracking-wider text-white/30">
              Previous 7 Days
            </div>
            {lastWeekList.map(renderItem)}
          </div>
        )}

        {/* Older */}
        {olderList.length > 0 && (
          <div className="mb-3">
            <div className="px-2 mb-1.5 font-mono text-[10px] uppercase tracking-wider text-white/30">
              Older
            </div>
            {olderList.map(renderItem)}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-border/30 px-4 py-3 flex items-center justify-between text-white/30 font-mono text-[10px]">
        <span>{conversations.length} threads</span>
        <button
          onClick={() => navigate("/settings")}
          className="flex items-center gap-1 hover:text-white transition-colors"
        >
          <Settings className="h-3 w-3" />
          Settings
        </button>
      </div>
    </aside>
  );
}
