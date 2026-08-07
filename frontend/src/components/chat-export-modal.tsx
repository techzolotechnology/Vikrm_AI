import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Download, Upload, FileJson, FileText, X, AlertCircle } from "lucide-react";

import { useExportConversation, useImportConversation } from "@/hooks/use-chat";
import type { ChatMessage, ConversationDetail } from "@/types/chat";

interface ChatExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  conversation: ConversationDetail | null;
  messages: ChatMessage[];
  onImportSuccess: (conversationId: number) => void;
}

export function ChatExportModal({
  isOpen,
  onClose,
  conversation,
  messages,
  onImportSuccess,
}: ChatExportModalProps) {
  const [activeTab, setActiveTab] = useState<"export" | "import">("export");
  const [format, setFormat] = useState<"json" | "markdown" | "txt">("json");
  const [importError, setImportError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const exportConversation = useExportConversation();
  const importConversation = useImportConversation();

  if (!isOpen) return null;

  const handleDownloadExport = async () => {
    if (!conversation) return;
    if (format === "json") {
      const data = await exportConversation.mutateAsync(conversation.id);
      const str = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
      const anchor = document.createElement("a");
      anchor.setAttribute("href", str);
      anchor.setAttribute("download", `chat-${conversation.title.toLowerCase().replace(/\s+/g, "-")}.json`);
      anchor.click();
    } else if (format === "markdown") {
      const mdLines = [
        `# ${conversation.title}`,
        `*Date: ${new Date(conversation.created_at).toLocaleString()}*\n`,
        ...messages.map((m) => `### **${m.role.toUpperCase()}**\n${m.content}\n`),
      ];
      const str = "data:text/markdown;charset=utf-8," + encodeURIComponent(mdLines.join("\n"));
      const anchor = document.createElement("a");
      anchor.setAttribute("href", str);
      anchor.setAttribute("download", `chat-${conversation.title.toLowerCase().replace(/\s+/g, "-")}.md`);
      anchor.click();
    } else {
      const txt = messages.map((m) => `[${m.role.toUpperCase()}]: ${m.content}`).join("\n\n");
      const blob = new Blob([txt], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `chat-${conversation.title.toLowerCase().replace(/\s+/g, "-")}.txt`;
      a.click();
    }
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const text = e.target?.result as string;
        const parsed = JSON.parse(text);
        const imported = await importConversation.mutateAsync(parsed);
        onImportSuccess(imported.id);
        onClose();
      } catch (err) {
        setImportError("Invalid JSON file format.");
      }
    };
    reader.readAsText(file);
  };

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
          <div className="flex items-center justify-between border-b border-border/60 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab("export")}
                className={`text-sm font-bold font-display px-3 py-1 rounded-xl transition-all ${
                  activeTab === "export" ? "bg-primary/20 text-white border border-primary/30" : "text-white/40"
                }`}
              >
                Export Chat
              </button>
              <button
                onClick={() => setActiveTab("import")}
                className={`text-sm font-bold font-display px-3 py-1 rounded-xl transition-all ${
                  activeTab === "import" ? "bg-primary/20 text-white border border-primary/30" : "text-white/40"
                }`}
              >
                Import Chat
              </button>
            </div>
            <button onClick={onClose} className="text-white/40 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>

          {activeTab === "export" ? (
            <div className="space-y-4">
              <p className="text-xs text-white/50">Choose export format for this conversation thread:</p>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: "json", label: "JSON", desc: "Full structured data", icon: FileJson },
                  { id: "markdown", label: "Markdown", desc: "For docs & Notion", icon: FileText },
                  { id: "txt", label: "Plain Text", desc: "Raw transcript", icon: FileText },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setFormat(item.id as any)}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all text-center ${
                      format === item.id ? "bg-primary/20 border-primary text-white" : "border-border/60 bg-background/40 text-white/50 hover:text-white"
                    }`}
                  >
                    <item.icon className="h-5 w-5 text-accent" />
                    <span className="text-xs font-bold">{item.label}</span>
                  </button>
                ))}
              </div>

              <button
                onClick={handleDownloadExport}
                className="w-full btn-primary text-xs py-3 rounded-xl"
              >
                <Download className="h-4 w-4" />
                Download {format.toUpperCase()}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-xs text-white/50">Upload a previously exported conversation JSON file:</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files)}
              />

              <div
                onClick={() => fileInputRef.current?.click()}
                className="flex flex-col items-center justify-center p-8 rounded-2xl border-2 border-dashed border-border/80 bg-background/50 hover:border-primary/50 cursor-pointer transition-all text-center"
              >
                <Upload className="h-8 w-8 text-primary mb-2" />
                <span className="text-xs font-semibold text-white/80">Click to select JSON file</span>
                <span className="text-[10px] text-white/30 mt-1">Supports Vikrm Chat export format</span>
              </div>

              {importError && (
                <div className="flex items-center gap-2 text-xs text-danger border border-danger/30 bg-danger/10 p-3 rounded-xl">
                  <AlertCircle className="h-4 w-4" />
                  {importError}
                </div>
              )}
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
