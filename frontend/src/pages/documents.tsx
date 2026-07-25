import { useRef, useState, type DragEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  Search,
  Trash2,
  Upload,
  X,
  Database,
  File,
  FileSpreadsheet,
} from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageTransition } from "@/components/page-transition";
import {
  useDeleteDocument,
  useDocuments,
  useSearchDocuments,
  useUploadDocument,
} from "@/hooks/use-documents";
import { cn } from "@/lib/utils";
import type { DocumentChunkResult } from "@/types/document";

const SUPPORTED_EXTENSIONS = [".txt", ".md", ".pdf", ".docx", ".csv"];

const STATUS_CONFIG = {
  processing: {
    icon: <Loader2 className="h-4 w-4 animate-spin text-accent" strokeWidth={2} />,
    label: "Processing",
    color: "text-accent",
    bg: "bg-accent/10 border-accent/20",
  },
  ready: {
    icon: <CheckCircle2 className="h-4 w-4 text-success" strokeWidth={1.75} />,
    label: "Ready",
    color: "text-success",
    bg: "bg-success/10 border-success/20",
  },
  failed: {
    icon: <AlertCircle className="h-4 w-4 text-danger" strokeWidth={1.75} />,
    label: "Failed",
    color: "text-danger",
    bg: "bg-danger/10 border-danger/20",
  },
};

function FileIcon({ filename }: { filename: string }) {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "csv") return <FileSpreadsheet className="h-4 w-4 text-emerald-400" strokeWidth={1.75} />;
  if (ext === "pdf") return <FileText className="h-4 w-4 text-red-400" strokeWidth={1.75} />;
  if (ext === "docx") return <FileText className="h-4 w-4 text-blue-400" strokeWidth={1.75} />;
  return <File className="h-4 w-4 text-white/40" strokeWidth={1.75} />;
}

export function Documents() {
  const { data: documents = [], isLoading } = useDocuments();
  const uploadDocument = useUploadDocument();
  const deleteDocument = useDeleteDocument();
  const searchDocuments = useSearchDocuments();

  const [isDragging, setIsDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DocumentChunkResult[] | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach((file) => uploadDocument.mutate(file));
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    searchDocuments.mutate(
      { query: searchQuery.trim(), top_k: 5 },
      { onSuccess: (data) => setSearchResults(data) },
    );
  };

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        <div className="mx-auto max-w-4xl">
          {/* Page Header */}
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="page-icon-wrap" style={{ background: "linear-gradient(135deg, rgba(245,158,11,0.2) 0%, rgba(234,179,8,0.1) 100%)", borderColor: "rgba(245,158,11,0.3)" }}>
                <FileText className="h-5 w-5" style={{ color: "#F59E0B" }} strokeWidth={1.75} />
              </div>
              <div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
                  Knowledge Base
                </span>
                <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                  RAG Vault
                </h1>
                <p className="text-sm text-white/40">
                  Upload documents for semantic search and AI citation.
                </p>
              </div>
            </div>
            {documents.length > 0 && (
              <span className="font-mono text-[11px] text-white/30">
                {documents.length} document{documents.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {/* Upload Zone */}
          <motion.div
            animate={{
              borderColor: isDragging ? "rgba(124,58,237,0.8)" : "rgba(255,255,255,0.12)",
              backgroundColor: isDragging ? "rgba(124,58,237,0.08)" : "rgba(255,255,255,0.02)",
            }}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="mb-6 flex cursor-pointer flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed p-10 text-center transition-all backdrop-blur-xl relative overflow-hidden"
          >
            {/* Animated glow */}
            <AnimatePresence>
              {isDragging && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-primary/5 rounded-2xl"
                  style={{ boxShadow: "inset 0 0 60px rgba(124,58,237,0.15)" }}
                />
              )}
            </AnimatePresence>

            <motion.div
              animate={{ y: isDragging ? -8 : 0, scale: isDragging ? 1.1 : 1 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className="flex h-14 w-14 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10"
            >
              <Upload className="h-7 w-7 text-accent" strokeWidth={1.5} />
            </motion.div>

            <div>
              <p className="text-sm font-semibold text-white">
                {isDragging ? "Release to upload" : "Drag & drop files here"}
              </p>
              <p className="mt-1 text-xs text-white/40">
                or <span className="text-accent underline">browse files</span>
              </p>
              <p className="mt-2 font-mono text-[11px] text-white/25">
                {SUPPORTED_EXTENSIONS.join(" · ")}
              </p>
            </div>

            {uploadDocument.isPending && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-2 text-xs text-accent"
              >
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Uploading & processing...
              </motion.div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={SUPPORTED_EXTENSIONS.join(",")}
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </motion.div>

          {/* Semantic Search */}
          <div className="mb-6 flex gap-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Semantic vector search across knowledge base..."
                className="input pl-10 text-xs"
              />
            </div>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleSearch}
              className="btn-primary text-xs px-5"
            >
              {searchDocuments.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                "Search"
              )}
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

          {/* Search Results */}
          <AnimatePresence>
            {searchResults && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                className="mb-6 space-y-3"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-mono text-[11px] text-white/40">
                    {searchResults.length} result{searchResults.length !== 1 ? "s" : ""} found
                  </span>
                </div>
                {searchResults.length === 0 && (
                  <p className="py-6 text-center text-xs text-white/30">No matching vector chunks found.</p>
                )}
                {searchResults.map((result, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="glass-card p-4 border border-primary/20"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <FileIcon filename={result.filename} />
                      <span className="font-mono text-xs text-accent">{result.filename}</span>
                      <span className="font-mono text-[10px] text-white/30">chunk #{result.chunk_index}</span>
                    </div>
                    <p className="text-xs text-white/80 leading-relaxed">{result.content}</p>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Document List */}
          {!searchResults && (
            <>
              {isLoading && (
                <div className="space-y-2.5">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="glass-card h-16 skeleton" />
                  ))}
                </div>
              )}

              {!isLoading && documents.length === 0 && (
                <EmptyState
                  icon={Database}
                  title="Knowledge Base is Empty"
                  description="Upload text documents, PDFs, or CSV files above to enable RAG citations during chat."
                />
              )}

              <div className="space-y-2.5">
                {documents.map((doc, index) => {
                  const cfg = STATUS_CONFIG[doc.status] ?? STATUS_CONFIG.processing;
                  return (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.04 }}
                      className="glass-card group flex items-center justify-between gap-4 p-4 border border-border/70 hover:border-white/15 transition-all duration-200"
                    >
                      <div className="flex min-w-0 items-center gap-3.5">
                        <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border", cfg.bg)}>
                          <FileIcon filename={doc.filename} />
                        </div>

                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-white">{doc.filename}</p>
                          <p className="font-mono text-[11px] text-white/35 mt-0.5">
                            {doc.status === "ready"
                              ? `${doc.chunk_count} chunks · ${doc.char_count.toLocaleString()} chars`
                              : doc.status === "failed"
                                ? doc.error
                                : "Chunking & embedding..."}
                          </p>
                        </div>
                      </div>

                      <div className="flex shrink-0 items-center gap-2.5">
                        <div className={cn("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold font-mono", cfg.bg, cfg.color)}>
                          {cfg.icon}
                          {cfg.label}
                        </div>
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => deleteDocument.mutate(doc.id)}
                          className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/30 hover:text-danger hover:border-danger/30 transition-all opacity-0 group-hover:opacity-100"
                          aria-label="Delete document"
                        >
                          <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                        </motion.button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </PageTransition>
  );
}
