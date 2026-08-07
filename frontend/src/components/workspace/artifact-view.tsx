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
    <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/90 text-slate-200 my-2 shadow-lg">
      {/* Artifact Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-950/80 border-b border-slate-800 select-none">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-slate-400 hover:text-slate-200"
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          <FileCode2 className="w-4 h-4 text-indigo-400" />
          <span className="font-mono text-xs font-semibold text-slate-200">{file.path}</span>
          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300">
            {file.language || "text"}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition-colors"
            title="Copy content"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition-colors"
            title="Download file"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download</span>
          </button>
        </div>
      </div>

      {/* Code Block Content */}
      {!isCollapsed && (
        <div className="p-3 bg-slate-950/40 overflow-x-auto text-xs font-mono">
          <pre className="text-slate-300 leading-relaxed whitespace-pre font-mono">
            {file.content}
          </pre>
        </div>
      )}
    </div>
  );
}
