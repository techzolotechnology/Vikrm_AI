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
  Edit2,
  Eye,
  Check,
  RefreshCw,
  BarChart3,
  AlertTriangle,
} from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageTransition } from "@/components/page-transition";
import { Tooltip } from "@/components/ui/tooltip";
import {
  useDeleteDocument,
  useDocuments,
  useRenameDocument,
  useDocumentContent,
  useSearchDocuments,
  useUploadDocument,
} from "@/hooks/use-documents";
import { cn } from "@/lib/utils";
import { workspaceApi } from "@/lib/workspace-api";
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
  if (ext === "md") return <FileText className="h-4 w-4 text-purple-400" strokeWidth={1.75} />;
  return <File className="h-4 w-4 text-white/40" strokeWidth={1.75} />;
}

// ─── Delete Confirmation ───────────────────────────────────────────────────────

function DeleteConfirm({ filename, onConfirm, onCancel }: { filename: string; onConfirm: () => void; onCancel: () => void }) {
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
            <AlertTriangle className="h-5 w-5 text-danger" />
          </div>
          <div>
            <h3 className="font-display text-sm font-bold text-white">Delete Document</h3>
            <p className="text-xs text-white/50">All chunks and embeddings will be removed.</p>
          </div>
        </div>
        <p className="text-sm text-white/70 mb-5 leading-relaxed">
          Delete <span className="font-mono text-white font-semibold">{filename}</span>? This will remove all vector embeddings and cannot be undone.
        </p>
        <div className="flex gap-3">
          <button onClick={onCancel} className="flex-1 rounded-xl border border-border/60 bg-surface/60 px-4 py-2 text-xs font-medium text-white/70 hover:text-white transition-colors">
            Cancel
          </button>
          <button onClick={onConfirm} className="flex-1 rounded-xl bg-danger/90 px-4 py-2 text-xs font-bold text-white hover:bg-danger transition-colors">
            Delete Document
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function Documents() {
  const { data: documents = [], isLoading } = useDocuments();
  const uploadDocument = useUploadDocument();
  const deleteDocument = useDeleteDocument();
  const renameDocument = useRenameDocument();
  const searchDocuments = useSearchDocuments();

  const [isDragging, setIsDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DocumentChunkResult[] | null>(null);
  const [editingDocId, setEditingDocId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState("");
  const [previewDocId, setPreviewDocId] = useState<number | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  // Hugging Face Tab State
  const [activeTab, setActiveTab] = useState<"documents" | "huggingface">("documents");
  const [hfQuery, setHfQuery] = useState("llama");
  const [hfResults, setHfResults] = useState<any[]>([]);
  const [hfLoading, setHfLoading] = useState(false);

  const handleSearchHf = async () => {
    if (!hfQuery.trim()) return;
    setHfLoading(true);
    try {
      const res = await workspaceApi.searchHfModels(hfQuery);
      setHfResults(res);
    } catch (e) {
      console.error("HF search error:", e);
    } finally {
      setHfLoading(false);
    }
  };

  const { data: previewContent } = useDocumentContent(previewDocId);
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
    if (!searchQuery.trim()) { setSearchResults(null); return; }
    searchDocuments.mutate(
      { query: searchQuery.trim(), top_k: 5 },
      { onSuccess: (data) => setSearchResults(data) },
    );
  };

  const handleSaveRename = (docId: number) => {
    if (editingName.trim()) {
      renameDocument.mutate({ documentId: docId, filename: editingName.trim() });
      setEditingDocId(null);
    }
  };

  const handleReindex = (docId: number, filename: string) => {
    // Re-index = delete + mark for re-process (user re-uploads the file)
    // For now, we trigger delete and notify the user
    if (confirm(`Delete and re-index ${filename}? You will need to re-upload the file.`)) {
      deleteDocument.mutate(docId);
    }
  };

  // Statistics
  const stats = {
    total: documents.length,
    ready: documents.filter((d) => d.status === "ready").length,
    processing: documents.filter((d) => d.status === "processing").length,
    failed: documents.filter((d) => d.status === "failed").length,
    totalChunks: documents.filter((d) => d.status === "ready").reduce((s, d) => s + (d.chunk_count || 0), 0),
    totalChars: documents.filter((d) => d.status === "ready").reduce((s, d) => s + (d.char_count || 0), 0),
  };

  const docToDelete = documents.find((d) => d.id === deleteConfirmId);

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
                  background: "linear-gradient(135deg, rgba(245,158,11,0.2) 0%, rgba(234,179,8,0.1) 100%)",
                  borderColor: "rgba(245,158,11,0.3)",
                }}
              >
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
          </div>

          {/* Stats Bar */}
          {documents.length > 0 && (
            <div className="mb-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: "Documents", value: stats.total, color: "#F59E0B" },
                { label: "Indexed", value: stats.ready, color: "#22C55E" },
                { label: "Chunks", value: stats.totalChunks, color: "#7C3AED" },
                { label: "Characters", value: stats.totalChars.toLocaleString(), color: "#22D3EE" },
              ].map((s) => (
                <div key={s.label} className="glass-card border border-border/60 px-4 py-3">
                  <p className="font-mono text-[10px] text-white/35 mb-1">{s.label}</p>
                  <p className="font-display text-lg font-bold" style={{ color: s.color }}>{s.value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Tab Selector */}
          <div className="mb-6 flex gap-2 border-b border-white/10 pb-3">
            <button
              onClick={() => setActiveTab("documents")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${
                activeTab === "documents" ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" : "text-white/40 hover:text-white"
              }`}
            >
              Document Vault ({documents.length})
            </button>
            <button
              onClick={() => setActiveTab("huggingface")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${
                activeTab === "huggingface" ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" : "text-white/40 hover:text-white"
              }`}
            >
              Hugging Face Hub
            </button>
          </div>

          {activeTab === "huggingface" && (
            <div className="glass-card border border-border/60 p-6 mb-6 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-amber-400" />
                Hugging Face Open Source Models & Datasets
              </h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={hfQuery}
                  onChange={(e) => setHfQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearchHf()}
                  placeholder="Search Hugging Face Models (e.g. llama, deepseek, qwen)..."
                  className="flex-1 bg-slate-900 border border-border/60 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
                />
                <button
                  onClick={handleSearchHf}
                  disabled={hfLoading}
                  className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-xs font-semibold text-white transition flex items-center gap-1.5"
                >
                  {hfLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                  Search Hub
                </button>
              </div>

              {hfResults.length > 0 && (
                <div className="space-y-2 mt-4 max-h-60 overflow-y-auto">
                  {hfResults.map((item, idx) => (
                    <div key={idx} className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 flex items-center justify-between text-xs font-mono">
                      <span className="text-amber-300 font-semibold">{item.id}</span>
                      <span className="text-slate-500">Downloads: {item.downloads || "100k+"}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

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
              animate={{ y: isDragging ? -8 : 0, scale: isDragging ? 1.15 : 1 }}
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
              onChange={(e) => handleFiles((e.target as HTMLInputElement).files)}
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
                className="input pl-10 text-xs w-full"
              />
            </div>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleSearch}
              className="btn-primary text-xs px-5"
            >
              {searchDocuments.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Search"}
            </motion.button>
            {searchResults && (
              <motion.button
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                onClick={() => { setSearchResults(null); setSearchQuery(""); }}
                className="flex items-center gap-1.5 rounded-xl border border-border px-3 text-xs text-white/50 hover:text-white transition-colors"
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
                  <BarChart3 className="h-4 w-4 text-accent" />
                  <span className="font-mono text-[11px] text-white/40">
                    {searchResults.length} vector chunk{searchResults.length !== 1 ? "s" : ""} found
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
                  const isEditingThis = editingDocId === doc.id;

                  return (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.04 }}
                      className="glass-card group flex items-center justify-between gap-4 p-4 border border-border/70 hover:border-white/15 transition-all duration-200"
                    >
                      <div className="flex min-w-0 flex-1 items-center gap-3.5">
                        <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border", cfg.bg)}>
                          <FileIcon filename={doc.filename} />
                        </div>

                        <div className="min-w-0 flex-1">
                          {isEditingThis ? (
                            <div className="flex items-center gap-2">
                              <input
                                value={editingName}
                                onChange={(e) => setEditingName(e.target.value)}
                                className="input text-xs font-semibold py-1 px-2"
                                autoFocus
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") handleSaveRename(doc.id);
                                  if (e.key === "Escape") setEditingDocId(null);
                                }}
                              />
                              <button onClick={() => handleSaveRename(doc.id)} className="p-1 text-success hover:text-white transition-colors">
                                <Check className="h-4 w-4" />
                              </button>
                              <button onClick={() => setEditingDocId(null)} className="p-1 text-white/40 hover:text-white transition-colors">
                                <X className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          ) : (
                            <p className="truncate text-sm font-semibold text-white">{doc.filename}</p>
                          )}
                          <p className="font-mono text-[11px] text-white/35 mt-0.5">
                            {doc.status === "ready"
                              ? `${doc.chunk_count} chunks · ${doc.char_count.toLocaleString()} chars`
                              : doc.status === "failed"
                                ? doc.error
                                : "Chunking & embedding..."}
                          </p>
                        </div>
                      </div>

                      <div className="flex shrink-0 items-center gap-2">
                        {/* Status badge */}
                        <div className={cn("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold font-mono", cfg.bg, cfg.color)}>
                          {cfg.icon}
                          {cfg.label}
                        </div>

                        {/* Preview */}
                        {doc.status === "ready" && (
                          <Tooltip content="Preview chunks" side="top">
                            <motion.button
                              whileHover={{ scale: 1.05 }}
                              onClick={() => setPreviewDocId(doc.id)}
                              className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/40 hover:text-accent transition-all opacity-0 group-hover:opacity-100"
                            >
                              <Eye className="h-3.5 w-3.5" />
                            </motion.button>
                          </Tooltip>
                        )}

                        {/* Re-index */}
                        {doc.status === "failed" && (
                          <Tooltip content="Re-index document" side="top">
                            <motion.button
                              whileHover={{ scale: 1.05 }}
                              onClick={() => handleReindex(doc.id, doc.filename)}
                              className="flex h-7 w-7 items-center justify-center rounded-lg border border-warning/30 bg-warning/10 text-warning transition-all opacity-0 group-hover:opacity-100"
                            >
                              <RefreshCw className="h-3.5 w-3.5" />
                            </motion.button>
                          </Tooltip>
                        )}

                        {/* Rename */}
                        <Tooltip content="Rename document" side="top">
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            onClick={() => { setEditingDocId(doc.id); setEditingName(doc.filename); }}
                            className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/40 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                          >
                            <Edit2 className="h-3.5 w-3.5" />
                          </motion.button>
                        </Tooltip>

                        {/* Delete */}
                        <Tooltip content="Delete document" side="top">
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => setDeleteConfirmId(doc.id)}
                            className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/30 hover:text-danger hover:border-danger/30 transition-all opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                          </motion.button>
                        </Tooltip>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </>
          )}

          {/* Document Content Preview Modal */}
          <AnimatePresence>
            {previewDocId && previewContent && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/70 backdrop-blur-md"
                onClick={() => setPreviewDocId(null)}
              >
                <motion.div
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.95, opacity: 0 }}
                  className="glass-card w-full max-w-2xl p-6 border border-border/80 shadow-2xl max-h-[80vh] flex flex-col"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="flex items-center justify-between pb-4 border-b border-border/50">
                    <div className="flex items-center gap-2">
                      <Eye className="h-4 w-4 text-accent" />
                      <h3 className="text-sm font-bold text-white">Preview: {previewContent.filename}</h3>
                      <span className="font-mono text-[10px] text-white/30">{previewContent.chunks.length} chunks</span>
                    </div>
                    <button onClick={() => setPreviewDocId(null)} className="text-white/40 hover:text-white transition-colors">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="mt-4 flex-1 overflow-y-auto space-y-3 no-scrollbar pr-1">
                    {previewContent.chunks.map((chunk, i) => (
                      <div key={i} className="rounded-xl border border-border/60 bg-surface/40 p-3.5 text-xs text-white/80 leading-relaxed font-mono">
                        <span className="text-[10px] text-accent/60 block mb-1 uppercase tracking-wider">Chunk #{i + 1}</span>
                        {chunk}
                      </div>
                    ))}
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Delete Confirm Dialog */}
          <AnimatePresence>
            {deleteConfirmId && docToDelete && (
              <DeleteConfirm
                filename={docToDelete.filename}
                onConfirm={() => { deleteDocument.mutate(deleteConfirmId); setDeleteConfirmId(null); }}
                onCancel={() => setDeleteConfirmId(null)}
              />
            )}
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  );
}
