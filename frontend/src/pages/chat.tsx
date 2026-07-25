import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, MessageSquare, AlertTriangle, Sparkles } from "lucide-react";

import { Composer } from "@/components/composer";
import { ConversationSidebar } from "@/components/conversation-sidebar";
import { MessageBubble } from "@/components/message-bubble";
import {
  useChatStream,
  useConversation,
  useConversations,
  useCreateConversation,
  useDeleteConversation,
} from "@/hooks/use-chat";
import { useAgents } from "@/hooks/use-agents";

export function Chat() {
  const { data: conversations = [] } = useConversations();
  const { data: agents = [] } = useAgents();
  const [activeId, setActiveId] = useState<number | null>(null);
  const { data: activeConversation } = useConversation(activeId);
  const createConversation = useCreateConversation();
  const deleteConversation = useDeleteConversation();
  const { localMessages, isStreaming, error, sendMessage, seedMessages } =
    useChatStream(activeId);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (activeId === null && conversations.length > 0) {
      setActiveId(conversations[0].id);
    }
  }, [activeId, conversations]);

  useEffect(() => {
    if (activeConversation) {
      seedMessages(activeConversation.messages);
    }
  }, [activeConversation, seedMessages]);

  useEffect(() => {
    if (autoScroll) {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [localMessages, autoScroll]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 80);
  };

  const handleCreate = (agentId: number | null) => {
    createConversation.mutate(
      agentId ? { agent_id: agentId } : {},
      {
        onSuccess: (conversation) => setActiveId(conversation.id),
      },
    );
  };

  const handleSend = async (content: string) => {
    let targetId = activeId;
    if (targetId === null) {
      const created = await createConversation.mutateAsync({});
      setActiveId(created.id);
      targetId = created.id;
    }
    setAutoScroll(true);
    await sendMessage(content, targetId);
  };

  const handleDelete = (id: number) => {
    deleteConversation.mutate(id, {
      onSuccess: () => {
        if (activeId === id) setActiveId(null);
      },
    });
  };

  const isEmpty = activeId === null && localMessages.length === 0;

  return (
    <div className="flex h-screen bg-background">
      <ConversationSidebar
        conversations={conversations}
        agents={agents}
        activeId={activeId}
        onSelect={setActiveId}
        onCreate={handleCreate}
        onDelete={handleDelete}
        isCreating={createConversation.isPending}
      />

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Chat Header */}
        <div className="flex shrink-0 items-center justify-between border-b border-border/60 bg-surface/20 px-6 py-3.5 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl border border-primary/30 bg-primary/10">
              <MessageSquare className="h-4 w-4 text-accent" strokeWidth={1.75} />
            </div>
            <div>
              <h2 className="font-display text-sm font-bold text-white leading-tight">
                {activeConversation?.title ?? "Vikrm AI Assistant"}
              </h2>
              {activeConversation && (
                <p className="flex items-center gap-1.5 font-mono text-[11px] text-white/40">
                  <span>{activeConversation.provider}</span>
                  <span className="text-white/20">·</span>
                  <span className="text-accent">{activeConversation.model}</span>
                  {isStreaming && (
                    <>
                      <span className="text-white/20">·</span>
                      <motion.span
                        animate={{ opacity: [0.4, 1, 0.4] }}
                        transition={{ duration: 1.2, repeat: Infinity }}
                        className="text-success"
                      >
                        Generating...
                      </motion.span>
                    </>
                  )}
                </p>
              )}
            </div>
          </div>

          {/* Header right */}
          <div className="flex items-center gap-3">
            {localMessages.length > 0 && (
              <>
                <button
                  onClick={() => {
                    const text = localMessages
                      .map((m) => `[${m.role.toUpperCase()}]: ${m.content}`)
                      .join("\n\n");
                    const blob = new Blob([text], { type: "text/plain" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `transcript-${activeConversation?.title || "chat"}.txt`;
                    a.click();
                  }}
                  className="flex items-center gap-1 rounded-lg border border-border/60 bg-surface/60 px-2.5 py-1 text-[11px] font-medium text-white/60 hover:text-white hover:border-white/20 transition-all"
                  title="Download Chat Transcript"
                >
                  Download
                </button>
                <span className="font-mono text-[10px] text-white/25">
                  {localMessages.length} message{localMessages.length !== 1 ? "s" : ""}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Messages */}
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto no-scrollbar"
        >
          <AnimatePresence initial={false}>
            {isEmpty ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex h-full min-h-[calc(100vh-200px)] items-center justify-center p-8"
              >
                <div className="text-center max-w-md">
                  {/* Animated AI icon */}
                  <motion.div
                    animate={{ y: [0, -10, 0] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                    className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl border border-primary/20 bg-primary/10"
                  >
                    <Bot className="h-10 w-10 text-primary/60" strokeWidth={1.5} />
                  </motion.div>

                  <h2 className="font-display text-xl font-bold text-white mb-2">
                    Start a Conversation
                  </h2>
                  <p className="text-sm text-white/40 leading-relaxed mb-6">
                    Chat with your AI engine or select an agent from the sidebar.
                    Context, memory, and RAG citations are saved automatically.
                  </p>

                  <div className="flex flex-wrap justify-center gap-2">
                    {["Summarize project findings", "What can you help me with?", "Explain the RAG pipeline"].map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => handleSend(prompt)}
                        className="flex items-center gap-1.5 rounded-full border border-border/60 bg-surface/50 px-3.5 py-2 text-xs text-white/60 hover:border-primary/40 hover:text-white transition-all"
                      >
                        <Sparkles className="h-3 w-3 text-accent" />
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            ) : (
              <div key="messages" className="space-y-5 px-6 py-6">
                {localMessages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    isStreaming={isStreaming && message.role === "assistant" &&
                      message === localMessages[localMessages.length - 1]}
                  />
                ))}
              </div>
            )}
          </AnimatePresence>
        </div>

        {/* Error banner */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              className="mx-6 mb-2 flex items-center gap-2 rounded-xl border border-danger/40 bg-danger/10 px-4 py-2.5 text-xs text-danger"
            >
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Composer */}
        <div className="shrink-0 border-t border-border/40 bg-background/50 px-6 pb-6 pt-4 backdrop-blur-xl">
          <Composer onSend={handleSend} disabled={isStreaming} />
        </div>
      </div>
    </div>
  );
}
