import { useState } from "react";
import {
  Check,
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
  FileCode2,
} from "lucide-react";
import { ProjectFile } from "@/lib/workspace-api";

interface ArtifactViewProps {
  file: ProjectFile;
}

export function ArtifactView({ file }: ArtifactViewProps) {
  const [copied, setCopied] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(file.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([file.content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = file.path.split("/").pop() || "file";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="glass-card border border-border/60 overflow-hidden my-2 shadow-glass">
      {/* Artifact Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-background/80 border-b border-border/60 select-none">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-white/40 hover:text-white transition-colors"
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          <FileCode2 className="w-4 h-4 text-primary" />
          <span className="font-mono text-xs font-semibold text-white/80">{file.path}</span>
          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-surface/60 text-primary border border-border/60">
            {file.language || "text"}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2 py-1 text-xs text-white/40 hover:text-white hover:bg-surface/60 rounded transition-all duration-200"
            title="Copy content"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1 px-2 py-1 text-xs text-white/40 hover:text-white hover:bg-surface/60 rounded transition-all duration-200"
            title="Download file"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download</span>
          </button>
        </div>
      </div>

      {/* Code Block Content */}
      {!isCollapsed && (
        <div className="p-3 bg-background/40 overflow-x-auto text-xs font-mono">
          <pre className="text-white/70 leading-relaxed whitespace-pre font-mono">
            {file.content}
          </pre>
        </div>
      )}
    </div>
  );
}
