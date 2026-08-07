import { motion, AnimatePresence } from "framer-motion";
import { Activity, Bot, Calendar, Hash, MessageSquare, X } from "lucide-react";

import type { ChatMessage, ConversationDetail } from "@/types/chat";

interface ChatStatsModalProps {
  isOpen: boolean;
  onClose: () => void;
  conversation: ConversationDetail | null;
  messages: ChatMessage[];
}

export function ChatStatsModal({
  isOpen,
  onClose,
  conversation,
  messages,
}: ChatStatsModalProps) {
  if (!isOpen || !conversation) return null;

  const totalMessages = messages.length;
  const userMessages = messages.filter((m) => m.role === "user").length;
  const assistantMessages = messages.filter((m) => m.role === "assistant").length;

  const totalWords = messages.reduce(
    (acc, m) => acc + (m.content ? m.content.trim().split(/\s+/).length : 0),
    0,
  );
  const totalChars = messages.reduce((acc, m) => acc + m.content.length, 0);

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4" onClick={onClose}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="relative w-full max-w-md rounded-2xl border border-border/80 bg-surface p-6 shadow-2xl overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border/60 pb-4 mb-5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 border border-primary/30">
                <Activity className="h-4 w-4 text-primary" />
              </div>
              <div>
                <h3 className="font-display text-base font-bold text-white">Thread Analytics</h3>
                <p className="font-mono text-[10px] text-white/40">{conversation.title}</p>
              </div>
            </div>
            <button onClick={onClose} className="text-white/40 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="rounded-xl border border-border/60 bg-background/50 p-3.5">
              <div className="flex items-center gap-2 text-white/40 text-xs mb-1">
                <MessageSquare className="h-3.5 w-3.5 text-accent" />
                <span>Total Turns</span>
              </div>
              <p className="font-display text-xl font-bold text-white">{totalMessages}</p>
              <p className="text-[10px] text-white/30 font-mono">
                {userMessages} user · {assistantMessages} AI
              </p>
            </div>

            <div className="rounded-xl border border-border/60 bg-background/50 p-3.5">
              <div className="flex items-center gap-2 text-white/40 text-xs mb-1">
                <Hash className="h-3.5 w-3.5 text-success" />
                <span>Total Words</span>
              </div>
              <p className="font-display text-xl font-bold text-white">{totalWords.toLocaleString()}</p>
              <p className="text-[10px] text-white/30 font-mono">
                ~{totalChars.toLocaleString()} characters
              </p>
            </div>

            <div className="rounded-xl border border-border/60 bg-background/50 p-3.5">
              <div className="flex items-center gap-2 text-white/40 text-xs mb-1">
                <Bot className="h-3.5 w-3.5 text-primary" />
                <span>Model Engine</span>
              </div>
              <p className="font-display text-sm font-bold text-white truncate">{conversation.model}</p>
              <p className="text-[10px] text-white/30 font-mono">{conversation.provider}</p>
            </div>

            <div className="rounded-xl border border-border/60 bg-background/50 p-3.5">
              <div className="flex items-center gap-2 text-white/40 text-xs mb-1">
                <Calendar className="h-3.5 w-3.5 text-warning" />
                <span>Created Date</span>
              </div>
              <p className="font-display text-xs font-bold text-white">
                {new Date(conversation.created_at).toLocaleDateString()}
              </p>
              <p className="text-[10px] text-white/30 font-mono">
                {new Date(conversation.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-full btn-glass text-xs py-2.5 rounded-xl"
          >
            Close
          </button>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
