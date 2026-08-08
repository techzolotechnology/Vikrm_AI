import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  MessageSquare,
  AlertTriangle,
  Download,
  Activity,
  Code2,
  FileText,
  LineChart,
  Brain,
  Bug,
  Zap,
  BookOpen,
  Languages,
  Menu,
  ChevronDown,
  Square,
} from "lucide-react";

import { ChatExportModal } from "@/components/chat-export-modal";
import { ChatStatsModal } from "@/components/chat-stats-modal";
import { Composer } from "@/components/composer";
import { ConversationSidebar } from "@/components/conversation-sidebar";
import { ErrorBoundary } from "@/components/error-boundary";
import { MessageBubble } from "@/components/message-bubble";
import { useAgents } from "@/hooks/use-agents";
import { useProviders } from "@/hooks/use-providers";
import {
  useChatStream,
  useConversation,
  useConversations,
  useCreateConversation,
  useDeleteConversation,
} from "@/hooks/use-chat";

const SUGGESTION_CARDS = [
  { icon: Code2, label: "Generate Code", prompt: "Write a clean TypeScript function that implements a debounce utility with proper types and JSDoc comments.", color: "#7C3AED" },
  { icon: FileText, label: "Explain Document", prompt: "Analyze the attached document and summarize the key findings, main arguments, and any conclusions.", color: "#22D3EE" },
  { icon: LineChart, label: "Analyze Data", prompt: "Perform statistical analysis on this dataset and identify trends, outliers, and key insights.", color: "#22C55E" },
  { icon: Brain, label: "Deep Research", prompt: "Conduct a comprehensive research overview on the latest advances in large language models and their practical applications.", color: "#EC4899" },
  { icon: Bug, label: "Debug Code", prompt: "Review this code for bugs, security vulnerabilities, and performance bottlenecks. Suggest specific fixes.", color: "#EF4444" },
  { icon: Zap, label: "Optimize", prompt: "Analyze this code for memory leaks, speed bottlenecks, and suggest concrete optimizations with examples.", color: "#F59E0B" },
  { icon: BookOpen, label: "Write Docs", prompt: "Generate comprehensive API documentation with usage examples, parameters, return values, and edge cases.", color: "#06B6D4" },
  { icon: Languages, label: "Translate", prompt: "Translate the following text to English while preserving the original tone, nuance, and cultural context.", color: "#8B5CF6" },
];

export function Chat() {
  const { data: conversations = [] } = useConversations();
  const { data: agents = [] } = useAgents();
  const [activeId, setActiveId] = useState<number | null>(null);
  const { data: activeConversation } = useConversation(activeId);
  const createConversation = useCreateConversation();
  const deleteConversation = useDeleteConversation();

  const { localMessages = [], isStreaming, error, sendMessage, seedMessages, stopStreaming } =
    useChatStream(activeId);

  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    if (activeId === null && conversations.length > 0) {
      setActiveId(conversations[0].id);
    }
  }, [activeId, conversations]);

  useEffect(() => {
    if (activeConversation && activeConversation.messages) {
      seedMessages(activeConversation.messages);
    }
  }, [activeConversation, seedMessages]);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [localMessages, autoScroll]);

  // Keyboard shortcut: Ctrl+N → new chat
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "n") {
        e.preventDefault();
        handleCreate(null);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 80;
    setAutoScroll(isNearBottom);
    setShowScrollButton(!isNearBottom);
  };

  const scrollToBottom = () => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    setAutoScroll(true);
    setShowScrollButton(false);
  };

  const handleEnsureConversation = async (): Promise<number> => {
    if (activeId !== null) return activeId;
    const created = await createConversation.mutateAsync({});
    setActiveId(created.id);
    return created.id;
  };

  const handleCreate = (agentId: number | null) => {
    createConversation.mutate(
      agentId ? { agent_id: agentId } : {},
      {
        onSuccess: (conversation) => {
          setActiveId(conversation.id);
          setMobileSidebarOpen(false);
        },
      },
    );
  };

  const handleSend = async (content: string, attachmentIds?: number[]) => {
    let targetId = activeId;
    if (targetId === null) {
      targetId = await handleEnsureConversation();
    }
    setAutoScroll(true);
    await sendMessage(content, targetId, attachmentIds);
  };

  const handleDelete = (id: number) => {
    deleteConversation.mutate(id, {
      onSuccess: () => {
        if (activeId === id) setActiveId(null);
      },
    });
  };

  const handleEditMessage = (_: number, newContent: string) => {
    handleSend(newContent);
  };

  const handleRetry = () => {
    const lastUserMessage = [...(localMessages || [])].reverse().find((m) => m.role === "user");
    if (lastUserMessage) {
      handleSend(lastUserMessage.content);
    }
  };

  const isEmpty = activeId === null || (localMessages || []).length === 0;

  const { providerModels, providerList, ollamaOnline } = useProviders();
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("qwen3:8b");

  useEffect(() => {
    if (providerList.length > 0 && !providerList.includes(selectedProvider)) {
      const firstProv = providerList[0];
      setSelectedProvider(firstProv);
      if (providerModels[firstProv]?.length > 0) {
        setSelectedModel(providerModels[firstProv][0]);
      }
    }
  }, [providerList, providerModels, selectedProvider]);

  return (
    <ErrorBoundary fallbackTitle="Chat Application Error">
      <div className="flex h-screen bg-background text-white overflow-hidden">
        {/* Desktop Sidebar */}
        <div className="hidden lg:block h-full">
          <ErrorBoundary fallbackTitle="Sidebar Error">
            <ConversationSidebar
              conversations={conversations}
              agents={agents}
              activeId={activeId}
              onSelect={(id) => { setActiveId(id); setMobileSidebarOpen(false); }}
              onCreate={handleCreate}
              onDelete={handleDelete}
              isCreating={createConversation.isPending}
            />
          </ErrorBoundary>
        </div>

        {/* Mobile Sidebar Drawer */}
        <AnimatePresence>
          {mobileSidebarOpen && (
            <div className="fixed inset-0 z-50 flex lg:hidden bg-black/60 backdrop-blur-sm">
              <motion.div
                initial={{ x: -280 }}
                animate={{ x: 0 }}
                exit={{ x: -280 }}
                transition={{ duration: 0.25 }}
                className="h-full"
              >
                <ErrorBoundary fallbackTitle="Sidebar Error">
                  <ConversationSidebar
                    conversations={conversations}
                    agents={agents}
                    activeId={activeId}
                    onSelect={(id) => { setActiveId(id); setMobileSidebarOpen(false); }}
                    onCreate={handleCreate}
                    onDelete={handleDelete}
                    isCreating={createConversation.isPending}
                  />
                </ErrorBoundary>
              </motion.div>
              <div className="flex-1" onClick={() => setMobileSidebarOpen(false)} />
            </div>
          )}
        </AnimatePresence>

        <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
          {/* Header */}
          <div className="flex shrink-0 items-center justify-between border-b border-border/60 bg-surface/20 px-6 py-3.5 backdrop-blur-xl">
            <div className="flex items-center gap-3">
              {/* Mobile menu trigger */}
              <button
                onClick={() => setMobileSidebarOpen(true)}
                className="lg:hidden p-1.5 rounded-xl border border-border/60 bg-surface/60 text-white/60 hover:text-white transition-colors"
              >
                <Menu className="h-4 w-4" />
              </button>

              <div className="flex h-9 w-9 items-center justify-center rounded-2xl border border-primary/30 bg-primary/10">
                <MessageSquare className="h-4 w-4 text-accent" strokeWidth={1.75} />
              </div>
              <div>
                <h2 className="font-display text-sm font-bold text-white leading-tight">
                  {activeConversation?.title ?? "Vikrm AI Assistant"}
                </h2>
                <div className="flex items-center gap-2 mt-0.5">
                  <select
                    value={selectedProvider}
                    onChange={(e) => {
                      const prov = e.target.value;
                      setSelectedProvider(prov);
                      if (providerModels[prov]?.length > 0) {
                        setSelectedModel(providerModels[prov][0]);
                      }
                    }}
                    className="bg-surface/80 border border-border/60 rounded-lg px-2 py-0.5 text-[11px] font-mono text-cyan-400 focus:outline-none"
                  >
                    {providerList.map((p) => (
                      <option key={p} value={p}>
                        {p.charAt(0).toUpperCase() + p.slice(1)}
                      </option>
                    ))}
                  </select>

                  {selectedProvider === "ollama" && !ollamaOnline ? (
                    <span className="text-[11px] font-mono text-amber-400 border border-amber-400/30 bg-amber-400/10 rounded-lg px-2 py-0.5">
                      ⚠️ Ollama is not running.
                    </span>
                  ) : (
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="bg-surface/80 border border-border/60 rounded-lg px-2 py-0.5 text-[11px] font-mono text-purple-300 focus:outline-none"
                    >
                      {(providerModels[selectedProvider] || ["qwen3:8b"]).map((m) => (
                        <option key={m} value={m}>
                          {m}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
            </div>

            {/* Header Actions */}
            <div className="flex items-center gap-2">
              {/* Stop Generation */}
              <AnimatePresence>
                {isStreaming && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    onClick={stopStreaming}
                    className="flex items-center gap-1.5 rounded-xl border border-danger/40 bg-danger/10 px-3 py-1.5 text-xs text-danger hover:bg-danger/20 transition-all"
                  >
                    <Square className="h-3 w-3" />
                    <span className="hidden sm:inline font-medium">Stop</span>
                  </motion.button>
                )}
              </AnimatePresence>

              {activeConversation && (
                <>
                  <button
                    onClick={() => setShowStatsModal(true)}
                    className="flex items-center gap-1.5 rounded-xl border border-border/60 bg-surface/60 px-3 py-1.5 text-xs text-white/60 hover:text-white hover:border-white/20 transition-all"
                    title="Thread analytics"
                  >
                    <Activity className="h-3.5 w-3.5 text-accent" />
                    <span className="hidden sm:inline font-medium">Stats</span>
                  </button>

                  <button
                    onClick={() => setShowExportModal(true)}
                    className="flex items-center gap-1.5 rounded-xl border border-border/60 bg-surface/60 px-3 py-1.5 text-xs text-white/60 hover:text-white hover:border-white/20 transition-all"
                    title="Export / Import thread"
                  >
                    <Download className="h-3.5 w-3.5 text-primary" />
                    <span className="hidden sm:inline font-medium">Export</span>
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Message Viewport */}
          <div
            ref={scrollRef}
            onScroll={handleScroll}
            className="relative flex-1 overflow-y-auto no-scrollbar"
          >
            <ErrorBoundary fallbackTitle="Messages Display Error">
              <AnimatePresence initial={false}>
                {isEmpty ? (
                  <motion.div
                    key="empty"
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6 md:p-10 max-w-4xl mx-auto text-center"
                  >
                    <motion.div
                      animate={{ y: [0, -8, 0] }}
                      transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                      className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl border border-primary/30 bg-primary/10 shadow-glow-md"
                    >
                      <Bot className="h-10 w-10 text-accent" strokeWidth={1.75} />
                    </motion.div>

                    <h2 className="font-display text-2xl font-extrabold text-white mb-2">
                      How can I help you today?
                    </h2>
                    <p className="text-sm text-white/50 leading-relaxed mb-8 max-w-lg">
                      Vikrm AI combines deep reasoning, long-term memory, document knowledge, and multi-agent orchestration.
                    </p>

                    {/* Suggestion Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 w-full mb-6">
                      {SUGGESTION_CARDS.map((card) => {
                        const Icon = card.icon;
                        return (
                          <motion.button
                            key={card.label}
                            whileHover={{ y: -3, scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => handleSend(card.prompt)}
                            className="glass-card flex flex-col items-start p-4 border border-border/70 hover:border-primary/40 text-left transition-all group cursor-pointer"
                          >
                            <div
                              className="flex h-8 w-8 items-center justify-center rounded-xl mb-3 transition-transform group-hover:scale-110"
                              style={{ backgroundColor: `${card.color}20`, border: `1px solid ${card.color}40` }}
                            >
                              <Icon className="h-4 w-4" style={{ color: card.color }} strokeWidth={1.75} />
                            </div>
                            <span className="font-display text-xs font-bold text-white group-hover:text-accent transition-colors">
                              {card.label}
                            </span>
                            <span className="text-[11px] text-white/40 mt-1 line-clamp-2 leading-tight">
                              {card.prompt.substring(0, 60)}...
                            </span>
                          </motion.button>
                        );
                      })}
                    </div>

                    <p className="text-[11px] text-white/20 font-mono">
                      Press <kbd className="rounded bg-white/10 px-1.5 py-0.5">Ctrl+N</kbd> for a new chat
                    </p>
                  </motion.div>
                ) : (
                  <div key="messages" className="space-y-6 px-6 py-6 max-w-4xl mx-auto pb-4">
                    {(localMessages || []).map((message) => (
                      <MessageBubble
                        key={message.id}
                        message={message}
                        conversationId={activeId}
                        isStreaming={
                          isStreaming &&
                          message.role === "assistant" &&
                          message === localMessages[localMessages.length - 1]
                        }
                        onEdit={handleEditMessage}
                        onRetry={handleRetry}
                      />
                    ))}
                  </div>
                )}
              </AnimatePresence>
            </ErrorBoundary>

            {/* Scroll to Bottom Button */}
            <AnimatePresence>
              {showScrollButton && (
                <motion.button
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                  onClick={scrollToBottom}
                  className="fixed bottom-28 right-8 z-20 flex h-9 w-9 items-center justify-center rounded-full border border-border/80 bg-surface/90 text-white/60 shadow-xl backdrop-blur-xl hover:text-white hover:border-primary/40 transition-all"
                >
                  <ChevronDown className="h-4 w-4" />
                </motion.button>
              )}
            </AnimatePresence>
          </div>

          {/* Error Banner */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                className="mx-6 mb-2 flex items-center gap-2 rounded-xl border border-danger/40 bg-danger/10 px-4 py-2.5 text-xs text-danger"
              >
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                <span>{typeof error === "string" ? error : JSON.stringify(error)}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Composer */}
          <div className="shrink-0 border-t border-border/40 bg-background/60 px-6 pb-6 pt-4 backdrop-blur-xl">
            <div className="max-w-4xl mx-auto">
              <ErrorBoundary fallbackTitle="Composer Input Error">
                <Composer
                  onSend={handleSend}
                  disabled={isStreaming}
                  conversationId={activeId}
                  onEnsureConversation={handleEnsureConversation}
                  onStop={stopStreaming}
                />
              </ErrorBoundary>
            </div>
          </div>
        </div>

        {/* Modals */}
        <ChatStatsModal
          isOpen={showStatsModal}
          onClose={() => setShowStatsModal(false)}
          conversation={activeConversation || null}
          messages={localMessages || []}
        />
        <ChatExportModal
          isOpen={showExportModal}
          onClose={() => setShowExportModal(false)}
          conversation={activeConversation || null}
          messages={localMessages || []}
          onImportSuccess={(newId) => setActiveId(newId)}
        />
      </div>
    </ErrorBoundary>
  );
}
