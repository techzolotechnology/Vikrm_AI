import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Bot,
  Check,
  Copy,
  RefreshCw,
  Edit2,
  Trash2,
  Star,
  FileText,
  Download,
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeHighlight from "rehype-highlight";
import rehypeKatex from "rehype-katex";
import type { Components } from "react-markdown";
import "highlight.js/styles/github-dark.css";
import "katex/dist/katex.min.css";

import { useBookmarkMessage, useDeleteMessage } from "@/hooks/use-chat";
import { cn } from "@/lib/utils";
import { formatMessageContent } from "@/lib/format-content";
import { parseProjectArtifact } from "@/lib/parse-project-artifact";
import { ProjectCompletionCard } from "@/components/chat/project-completion-card";
import { useAuthStore } from "@/store/use-auth-store";
import { Tooltip } from "@/components/ui/tooltip";
import type { ChatMessage } from "@/types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
  conversationId?: number | null;
  isStreaming?: boolean;
  onEdit?: (messageId: number, newContent: string) => void;
  onRetry?: () => void;
}

// ─── Mermaid Diagram Component ────────────────────────────────────────────────

function MermaidDiagram({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [rendered, setRendered] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function render() {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          themeVariables: {
            primaryColor: "#7C3AED",
            primaryTextColor: "#fff",
            primaryBorderColor: "#7C3AED",
            lineColor: "#7C3AED",
            background: "#0d1117",
            mainBkg: "#161b22",
          },
        });
        const id = `mermaid-${Math.random().toString(36).slice(2)}`;
        const { svg } = await mermaid.render(id, code.trim());
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg;
          setRendered(true);
        }
      } catch (err: any) {
        if (!cancelled) setError(err?.message || "Diagram render failed");
      }
    }
    render();
    return () => { cancelled = true; };
  }, [code]);

  if (error) {
    return (
      <div className="my-3 rounded-xl border border-danger/30 bg-danger/5 p-3 text-xs text-danger/80 font-mono">
        <AlertCircle className="h-3.5 w-3.5 inline mr-2" />
        Mermaid: {error}
      </div>
    );
  }

  return (
    <div className="my-3 rounded-xl border border-border/60 bg-[#0d1117] p-4 overflow-x-auto">
      {!rendered && (
        <div className="flex items-center gap-2 text-xs text-white/40 font-mono">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="h-3 w-3 border border-accent/50 border-t-accent rounded-full" />
          Rendering diagram...
        </div>
      )}
      <div ref={ref} className="flex justify-center" />
    </div>
  );
}

// Helper to safely extract raw plain text from React children tree without String(children) array coercion
function extractText(node: any): string {
  if (node === null || node === undefined) return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (typeof node === "object" && node !== null && node.props) {
    return extractText(node.props.children);
  }
  return "";
}

function CodeBlock({
  language,
  code,
  highlightedChildren,
}: {
  language: string;
  code: string;
  highlightedChildren?: React.ReactNode;
}) {
  const [copied, setCopied] = useState(false);

  // Detect Mermaid diagrams
  if (language === "mermaid") {
    return <MermaidDiagram code={code} />;
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const extMap: Record<string, string> = {
      typescript: "ts", javascript: "js", python: "py", java: "java",
      bash: "sh", sh: "sh", shell: "sh", css: "css",
      html: "html", json: "json", yaml: "yml", sql: "sql",
    };
    const ext = extMap[language] ?? "txt";
    const blob = new Blob([code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `code.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="relative my-3 rounded-xl border border-border/80 bg-[#0d1117] overflow-hidden font-mono text-sm shadow-xl group/code">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/60 bg-[#161b22] px-4 py-2">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-danger/60" />
            <div className="h-3 w-3 rounded-full bg-warning/60" />
            <div className="h-3 w-3 rounded-full bg-success/60" />
          </div>
          <span className="text-xs font-semibold text-white/40 uppercase tracking-wider ml-1">
            {language || "code"}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Tooltip content="Download file" side="top">
            <button
              onClick={handleDownload}
              aria-label="Download code"
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] text-white/40 hover:bg-white/10 hover:text-white transition-all"
            >
              <Download className="h-3 w-3" />
            </button>
          </Tooltip>
          <Tooltip content={copied ? "Copied!" : "Copy code"} side="top">
            <button
              onClick={handleCopy}
              aria-label="Copy code"
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] text-white/40 hover:bg-white/10 hover:text-white transition-all"
            >
              {copied ? (
                <Check className="h-3 w-3 text-success" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
          </Tooltip>
        </div>
      </div>
      {/* Code */}
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed max-h-96">
        <code className={language ? `language-${language}` : ""}>
          {highlightedChildren || code}
        </code>
      </pre>
    </div>
  );
}

// ─── Markdown Components ───────────────────────────────────────────────────────

const markdownComponents: Components = {
  code({ className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || "");
    const language = match?.[1] ?? "";
    const rawCode = extractText(children).replace(/\n$/, "");
    const isBlock = rawCode.includes("\n") || !!className;

    if (isBlock) {
      return <CodeBlock language={language} code={rawCode} highlightedChildren={children} />;
    }

    return (
      <code
        className="rounded-md border border-border/60 bg-surface/80 px-1.5 py-0.5 font-mono text-[0.85em] text-accent"
        {...props}
      >
        {children}
      </code>
    );
  },
  h1: ({ children }) => <h1 className="mt-4 mb-2 font-display text-xl font-bold text-white border-b border-border/40 pb-2">{children}</h1>,
  h2: ({ children }) => <h2 className="mt-3 mb-2 font-display text-lg font-bold text-white/90">{children}</h2>,
  h3: ({ children }) => <h3 className="mt-2 mb-1 font-display text-base font-semibold text-white/80">{children}</h3>,
  h4: ({ children }) => <h4 className="mt-2 mb-1 font-semibold text-white/75 text-sm">{children}</h4>,
  p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed text-white/90">{children}</p>,
  ul: ({ children }) => <ul className="mb-3 ml-4 list-disc space-y-1 text-white/85">{children}</ul>,
  ol: ({ children }) => <ol className="mb-3 ml-4 list-decimal space-y-1 text-white/85">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-4 border-primary/60 bg-primary/5 pl-4 py-2 italic text-white/70 rounded-r-xl">
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto rounded-xl border border-border/60 shadow-sm">
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-surface/80 border-b border-border/60">{children}</thead>,
  tbody: ({ children }) => <tbody className="divide-y divide-border/30">{children}</tbody>,
  th: ({ children }) => <th className="px-4 py-2.5 text-left font-semibold text-white/80 text-xs uppercase tracking-wider">{children}</th>,
  td: ({ children }) => <td className="px-4 py-2.5 text-white/75">{children}</td>,
  hr: () => <hr className="my-4 border-border/30" />,
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-accent underline underline-offset-2 hover:text-accent/80 transition-colors"
    >
      {children}
    </a>
  ),
  strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
  em: ({ children }) => <em className="italic text-white/80">{children}</em>,
  del: ({ children }) => <del className="line-through text-white/50">{children}</del>,
  // Task list items
  input: ({ checked, ...props }) => (
    <input
      type="checkbox"
      checked={checked}
      readOnly
      className="mr-1.5 accent-primary rounded"
      {...props}
    />
  ),
};

// ─── Streaming Cursor ─────────────────────────────────────────────────────────

function StreamingCursor() {
  return (
    <motion.span
      animate={{ opacity: [1, 0, 1] }}
      transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut" }}
      className="ml-0.5 inline-block h-[1em] w-0.5 translate-y-[2px] rounded-full bg-accent"
    />
  );
}

// ─── Thinking Indicator ────────────────────────────────────────────────────────

function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-1.5 py-1 text-xs text-accent font-mono">
      {[0, 0.15, 0.3].map((delay, i) => (
        <motion.div
          key={i}
          animate={{ scale: [1, 1.4, 1], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 0.8, repeat: Infinity, delay }}
          className="h-1.5 w-1.5 rounded-full bg-accent"
        />
      ))}
      <span className="ml-1 text-white/40">Thinking...</span>
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────────

export function MessageBubble({
  message,
  conversationId,
  isStreaming,
  onEdit,
  onRetry,
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const user = useAuthStore((state) => state.user);
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message?.content ?? "");
  const [reaction, setReaction] = useState<"up" | "down" | null>(null);

  const bookmarkMessage = useBookmarkMessage();
  const deleteMessage = useDeleteMessage();

  const handleCopy = async () => {
    if (message?.content) {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleBookmark = () => {
    if (!conversationId || !message?.id) return;
    bookmarkMessage.mutate({ conversationId, messageId: message.id });
  };

  const handleDelete = () => {
    if (!conversationId || !message?.id) return;
    deleteMessage.mutate({ conversationId, messageId: message.id });
  };

  const handleSaveEdit = () => {
    if (onEdit && message?.id && editContent.trim()) {
      onEdit(message.id, editContent.trim());
      setIsEditing(false);
    }
  };

  const timestamp = new Date(message.created_at || Date.now()).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className={cn("group flex w-full gap-3", isUser ? "flex-row-reverse" : "flex-row")}
      role="article"
      aria-label={`${isUser ? "User" : "AI"} message`}
    >
      {/* Avatar */}
      <div className="shrink-0 mt-1">
        {isUser ? (
          user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt="Your avatar"
              className="h-8 w-8 rounded-full border border-primary/40 object-cover shadow-glow-sm"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-brand text-xs font-bold text-white shadow-glow-sm" aria-hidden>
              {(user?.full_name ?? user?.email ?? "U").charAt(0).toUpperCase()}
            </div>
          )
        ) : (
          <motion.div
            animate={isStreaming ? { scale: [1, 1.08, 1] } : {}}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="flex h-8 w-8 items-center justify-center rounded-2xl border border-primary/30 bg-primary/10 shadow-glow-sm"
            aria-label="AI assistant"
          >
            <Bot className="h-4 w-4 text-accent" strokeWidth={1.75} />
          </motion.div>
        )}
      </div>

      {/* Bubble Container */}
      <div className={cn("flex max-w-[85%] flex-col gap-1", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "relative rounded-2xl px-4 py-3.5 text-sm shadow-md transition-all",
            isUser
              ? "bg-primary text-white font-medium rounded-tr-sm"
              : "glass-card border border-border/80 text-white/90 rounded-tl-sm",
            message.error && "border-danger/60 bg-danger/10 text-danger",
          )}
        >
          {isEditing ? (
            <div className="flex flex-col gap-2 min-w-[280px]">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="input text-xs font-normal resize-none"
                rows={3}
                autoFocus
                aria-label="Edit message"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && e.ctrlKey) handleSaveEdit();
                  if (e.key === "Escape") setIsEditing(false);
                }}
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setIsEditing(false)}
                  className="rounded-lg px-2.5 py-1 text-xs text-white/60 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button onClick={handleSaveEdit} className="btn-primary text-xs px-3 py-1">
                  Save & Resend
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Message Content */}
              {message.content ? (
                isUser ? (
                  <div className="whitespace-pre-wrap break-words">{formatMessageContent(message.content)}</div>
                ) : (() => {
                  const artifact = parseProjectArtifact(message.content);
                  return (
                    <div className="prose-sm max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeHighlight, rehypeKatex]}
                        components={markdownComponents}
                      >
                        {formatMessageContent(artifact.isProject ? artifact.summaryText : message.content)}
                      </ReactMarkdown>

                      {/* Project Completion Artifact Card (Claude Code Style) */}
                      {artifact.isProject && (
                        <div className="mt-4 not-prose">
                          <ProjectCompletionCard artifact={artifact} />
                        </div>
                      )}

                      {isStreaming && <StreamingCursor />}
                    </div>
                  );
                })()
              ) : (
                isStreaming && <ThinkingIndicator />
              )}

              {/* Error State */}
              {message.error && (
                <div className="flex items-center gap-2 text-danger text-xs mt-2 rounded-lg bg-danger/10 px-2 py-1.5 border border-danger/20">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span>{message.error}</span>
                </div>
              )}

              {/* Attachment Preview */}
              {message.attachments && message.attachments.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2 pt-2 border-t border-white/10">
                  {message.attachments.map((att) => (
                    <div
                      key={att.id}
                      className="flex items-center gap-1.5 rounded-lg bg-black/30 px-2.5 py-1 text-[11px] font-mono text-white/80"
                    >
                      <FileText className="h-3 w-3 text-accent" />
                      <span>{att.filename}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Message Metadata Row */}
        <div className={cn(
          "flex items-center gap-2 px-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200",
          isUser ? "flex-row-reverse" : "flex-row",
        )}>
          {/* Timestamp */}
          <span className="font-mono text-[10px] text-white/25 select-none" aria-label={`Sent at ${timestamp}`}>
            {timestamp}
          </span>

          {!isEditing && (
            <div className={cn("flex items-center gap-0.5", isUser ? "flex-row-reverse" : "flex-row")}>
              {/* Copy */}
              <Tooltip content={copied ? "Copied!" : "Copy"} side="top">
                <button
                  onClick={handleCopy}
                  aria-label="Copy message"
                  className="flex items-center gap-1 rounded-lg p-1.5 text-white/30 hover:bg-white/10 hover:text-white transition-all"
                >
                  {copied ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
                </button>
              </Tooltip>

              {/* Bookmark */}
              {conversationId && message.id > 0 && (
                <Tooltip content={message.is_bookmarked ? "Remove bookmark" : "Bookmark"} side="top">
                  <button
                    onClick={handleBookmark}
                    aria-label={message.is_bookmarked ? "Remove bookmark" : "Bookmark message"}
                    className={cn(
                      "rounded-lg p-1.5 transition-all",
                      message.is_bookmarked
                        ? "text-warning"
                        : "text-white/30 hover:bg-white/10 hover:text-warning",
                    )}
                  >
                    <Star className="h-3 w-3" />
                  </button>
                </Tooltip>
              )}

              {/* Edit (user only) */}
              {isUser && onEdit && (
                <Tooltip content="Edit & resend" side="top">
                  <button
                    onClick={() => setIsEditing(true)}
                    aria-label="Edit message"
                    className="rounded-lg p-1.5 text-white/30 hover:bg-white/10 hover:text-white transition-all"
                  >
                    <Edit2 className="h-3 w-3" />
                  </button>
                </Tooltip>
              )}

              {/* Retry (assistant only) */}
              {!isUser && onRetry && (
                <Tooltip content="Regenerate response" side="top">
                  <button
                    onClick={onRetry}
                    aria-label="Regenerate response"
                    className="rounded-lg p-1.5 text-white/30 hover:bg-white/10 hover:text-accent transition-all"
                  >
                    <RefreshCw className="h-3 w-3" />
                  </button>
                </Tooltip>
              )}

              {/* Reactions (assistant only) */}
              {!isUser && (
                <>
                  <Tooltip content="Good response" side="top">
                    <button
                      onClick={() => setReaction(reaction === "up" ? null : "up")}
                      aria-label="Good response"
                      aria-pressed={reaction === "up"}
                      className={cn(
                        "rounded-lg p-1.5 transition-all",
                        reaction === "up" ? "text-success" : "text-white/30 hover:bg-white/10 hover:text-success",
                      )}
                    >
                      <ThumbsUp className="h-3 w-3" />
                    </button>
                  </Tooltip>
                  <Tooltip content="Bad response" side="top">
                    <button
                      onClick={() => setReaction(reaction === "down" ? null : "down")}
                      aria-label="Bad response"
                      aria-pressed={reaction === "down"}
                      className={cn(
                        "rounded-lg p-1.5 transition-all",
                        reaction === "down" ? "text-danger" : "text-white/30 hover:bg-white/10 hover:text-danger",
                      )}
                    >
                      <ThumbsDown className="h-3 w-3" />
                    </button>
                  </Tooltip>
                </>
              )}

              {/* Delete */}
              {conversationId && message.id > 0 && (
                <Tooltip content="Delete message" side="top">
                  <button
                    onClick={handleDelete}
                    aria-label="Delete message"
                    className="rounded-lg p-1.5 text-white/20 hover:bg-danger/10 hover:text-danger transition-all"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </Tooltip>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
