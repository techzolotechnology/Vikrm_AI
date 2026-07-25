import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Check, Copy, ThumbsDown, ThumbsUp, AlertTriangle, RefreshCw } from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/use-auth-store";
import type { ChatMessage } from "@/types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const user = useAuthStore((state) => state.user);
  const [copied, setCopied] = useState(false);
  const [reaction, setReaction] = useState<"up" | "down" | null>(null);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className={cn("flex w-full gap-3", isUser ? "flex-row-reverse" : "flex-row")}
    >
      {/* Avatar */}
      <div className="shrink-0 mt-1">
        {isUser ? (
          user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt=""
              className="h-8 w-8 rounded-full border border-primary/40 object-cover shadow-glow-sm"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-brand text-xs font-bold text-white shadow-glow-sm">
              {(user?.full_name ?? user?.email ?? "U").charAt(0).toUpperCase()}
            </div>
          )
        ) : (
          <motion.div
            animate={isStreaming ? { boxShadow: ["0 0 8px rgba(34,211,238,0.3)", "0 0 20px rgba(34,211,238,0.6)", "0 0 8px rgba(34,211,238,0.3)"] } : {}}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-primary/30 bg-surface/90"
          >
            <Bot className="h-4 w-4 text-accent" strokeWidth={1.75} />
          </motion.div>
        )}
      </div>

      {/* Bubble container */}
      <div className={cn("group relative flex flex-col max-w-[80%] sm:max-w-[72%]", isUser ? "items-end" : "items-start")}>
        <motion.div
          layout
          className={cn(
            "relative rounded-2xl px-4 py-3.5 text-sm leading-relaxed shadow-sm transition-all duration-200",
            isUser
              ? "message-user text-white rounded-tr-sm"
              : "message-assistant text-white/95 rounded-tl-sm",
          )}
        >
          {/* Streaming typing indicator */}
          {message.content.length === 0 && isStreaming ? (
            <div className="flex items-center gap-1.5 py-1 px-1">
              <motion.span
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                className="h-2 w-2 rounded-full bg-accent"
              />
              <motion.span
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0.15 }}
                className="h-2 w-2 rounded-full bg-accent"
              />
              <motion.span
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0.3 }}
                className="h-2 w-2 rounded-full bg-accent"
              />
            </div>
          ) : (
            <div className="whitespace-pre-wrap break-words">
              {message.content}
              {/* Streaming cursor */}
              {isStreaming && message.content.length > 0 && (
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  className="ml-0.5 inline-block h-4 w-0.5 align-middle bg-accent rounded-full"
                />
              )}
            </div>
          )}

          {message.error && (
            <div className="mt-2 flex items-center gap-1.5 font-mono text-xs text-danger">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              <span>{message.error}</span>
            </div>
          )}
        </motion.div>

        {/* Action toolbar for assistant messages */}
        <AnimatePresence>
          {!isUser && message.content.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 0, y: 0 }}
              whileHover={{ opacity: 1 }}
              className="mt-1.5 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            >
              <button
                onClick={handleCopy}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg border border-border/60 bg-surface/80 px-2.5 py-1 text-[10px] font-medium transition-all",
                  copied ? "text-success border-success/30" : "text-white/50 hover:text-white hover:border-white/20",
                )}
                title="Copy response"
              >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                {copied ? "Copied!" : "Copy"}
              </button>

              <button
                onClick={() => setReaction(reaction === "up" ? null : "up")}
                className={cn(
                  "flex items-center justify-center rounded-lg border border-border/60 bg-surface/80 p-1.5 text-[10px] transition-all",
                  reaction === "up" ? "text-success border-success/40 bg-success/10" : "text-white/40 hover:text-success hover:border-success/30",
                )}
                title="Good response"
              >
                <ThumbsUp className="h-3 w-3" />
              </button>

              <button
                onClick={() => setReaction(reaction === "down" ? null : "down")}
                className={cn(
                  "flex items-center justify-center rounded-lg border border-border/60 bg-surface/80 p-1.5 text-[10px] transition-all",
                  reaction === "down" ? "text-danger border-danger/40 bg-danger/10" : "text-white/40 hover:text-danger hover:border-danger/30",
                )}
                title="Poor response"
              >
                <ThumbsDown className="h-3 w-3" />
              </button>

              <button
                className="flex items-center justify-center rounded-lg border border-border/60 bg-surface/80 p-1.5 text-[10px] text-white/40 hover:text-white hover:border-white/20 transition-all"
                title="Regenerate"
              >
                <RefreshCw className="h-3 w-3" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
