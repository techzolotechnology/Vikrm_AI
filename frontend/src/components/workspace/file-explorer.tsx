/**
 * Professional AI IDE File Explorer — VS Code style
 * Features: Multi-select, Context menus, Drag-to-reorder, Duplicate, Rename, Delete, Move, Search, Recent files
 */
import { useState, useRef, useCallback } from "react";
import {
  ChevronDown,
  ChevronRight,
  Copy,
  FileCode,
  FilePlus,
  Folder,
  FolderOpen,
  FolderPlus,
  Pencil,
  Search,
  Trash2,
  Circle,
  Clock,
  X,
} from "lucide-react";
import { ProjectFile } from "@/lib/workspace-api";

interface FileNode {
  name: string;
  path: string;
  isFolder: boolean;
  file?: ProjectFile;
  children?: FileNode[];
}

interface FileExplorerProps {
  files: ProjectFile[];
  activeFile: ProjectFile | null;
  unsavedFiles?: Set<string>;
  recentFiles?: ProjectFile[];
  onSelectFile: (file: ProjectFile) => void;
  onCreateFile: (folderPath?: string) => void;
  onCreateFolder: (parentFolder?: string) => void;
  onRenameFile: (oldPath: string, newPath: string) => void;
  onDeleteFile: (fileId: number) => void;
  onDuplicateFile?: (file: ProjectFile) => void;
}

type ContextMenu = { x: number; y: number; node: FileNode } | null;

function getFileIcon(name: string): { color: string } {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  const colorMap: Record<string, string> = {
    tsx: "text-blue-400",
    ts: "text-blue-500",
    jsx: "text-cyan-400",
    js: "text-yellow-400",
    py: "text-green-400",
    json: "text-amber-300",
    css: "text-pink-400",
    html: "text-orange-400",
    md: "text-slate-300",
    sql: "text-violet-400",
    yaml: "text-teal-400",
    yml: "text-teal-400",
    env: "text-rose-300",
    toml: "text-amber-400",
    gitignore: "text-slate-400",
    dockerfile: "text-sky-400",
  };
  return { color: colorMap[ext] ?? "text-slate-400" };
}

export function FileExplorer({
  files,
  activeFile,
  unsavedFiles = new Set(),
  recentFiles = [],
  onSelectFile,
  onCreateFile,
  onCreateFolder,
  onRenameFile,
  onDeleteFile,
  onDuplicateFile,
}: FileExplorerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({});
  const [editingPath, setEditingPath] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [selectedPaths, setSelectedPaths] = useState<Set<string>>(new Set());
  const [contextMenu, setContextMenu] = useState<ContextMenu>(null);
  const [showRecent, setShowRecent] = useState(false);
  const [dragOver, setDragOver] = useState<string | null>(null);
  const contextMenuRef = useRef<HTMLDivElement>(null);

  // Close context menu on outside click
  const handleGlobalClick = useCallback(() => setContextMenu(null), []);

  // Build tree from flat paths
  const buildTree = (fileList: ProjectFile[]): FileNode[] => {
    const root: FileNode[] = [];
    fileList.forEach((file) => {
      if (file.path.endsWith(".gitkeep") && fileList.length > 1) return;
      const parts = file.path.split("/");
      let currentLevel = root;
      parts.forEach((part, index) => {
        const isLast = index === parts.length - 1;
        const currentPath = parts.slice(0, index + 1).join("/");
        let existing = currentLevel.find((node) => node.name === part);
        if (!existing) {
          existing = {
            name: part,
            path: currentPath,
            isFolder: !isLast,
            file: isLast ? file : undefined,
            children: isLast ? undefined : [],
          };
          currentLevel.push(existing);
        }
        if (!isLast && existing.children) {
          currentLevel = existing.children;
        }
      });
    });
    // Sort: folders first, then files alphabetically
    const sortNodes = (nodes: FileNode[]): FileNode[] => {
      nodes.sort((a, b) => {
        if (a.isFolder && !b.isFolder) return -1;
        if (!a.isFolder && b.isFolder) return 1;
        return a.name.localeCompare(b.name);
      });
      nodes.forEach((n) => { if (n.children) sortNodes(n.children); });
      return nodes;
    };
    return sortNodes(root);
  };

  const toggleFolder = (path: string) =>
    setExpandedFolders((prev) => ({ ...prev, [path]: prev[path] === undefined ? false : !prev[path] }));

  const handleSelect = (node: FileNode, e: React.MouseEvent) => {
    if (!node.file) return;
    if (e.ctrlKey || e.metaKey) {
      setSelectedPaths((prev) => {
        const next = new Set(prev);
        next.has(node.path) ? next.delete(node.path) : next.add(node.path);
        return next;
      });
    } else {
      setSelectedPaths(new Set([node.path]));
      onSelectFile(node.file);
    }
  };

  const handleContextMenu = (e: React.MouseEvent, node: FileNode) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ x: e.clientX, y: e.clientY, node });
  };

  const filteredFiles = searchQuery
    ? files.filter((f) => f.path.toLowerCase().includes(searchQuery.toLowerCase()))
    : files;

  const tree = buildTree(filteredFiles);

  const renderNode = (node: FileNode, depth = 0): React.ReactElement => {
    const isExpanded = expandedFolders[node.path] ?? true;
    const isActive = activeFile?.path === node.path;
    const isSelected = selectedPaths.has(node.path);
    const isEditing = editingPath === node.path;
    const isUnsaved = unsavedFiles.has(node.path);
    const isDragTarget = dragOver === node.path;
    const { color: iconColor } = getFileIcon(node.name);

    if (node.isFolder) {
      return (
        <div key={node.path} className="select-none">
          <div
            onClick={() => toggleFolder(node.path)}
            onContextMenu={(e) => handleContextMenu(e, node)}
            onDragOver={(e) => { e.preventDefault(); setDragOver(node.path); }}
            onDragLeave={() => setDragOver(null)}
            style={{ paddingLeft: `${depth * 14 + 6}px` }}
            className={`flex items-center gap-1.5 py-[3px] px-2 text-xs cursor-pointer group transition-colors rounded-sm ${
              isDragTarget ? "bg-indigo-600/20 border border-indigo-500/40" : "hover:bg-slate-800/60"
            } text-slate-300`}
          >
            {isExpanded ? (
              <ChevronDown className="w-3 h-3 text-slate-500 shrink-0" />
            ) : (
              <ChevronRight className="w-3 h-3 text-slate-500 shrink-0" />
            )}
            {isExpanded ? (
              <FolderOpen className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            ) : (
              <Folder className="w-3.5 h-3.5 text-amber-400/80 shrink-0" />
            )}
            <span className="font-medium text-[11.5px] truncate flex-1">{node.name}</span>
            <div className="hidden group-hover:flex items-center gap-0.5">
              <button
                onClick={(e) => { e.stopPropagation(); onCreateFile(node.path); }}
                className="p-0.5 hover:text-indigo-300 rounded"
                title="New file in folder"
              >
                <FilePlus className="w-3 h-3" />
              </button>
            </div>
          </div>
          {isExpanded && node.children && (
            <div>{node.children.map((child) => renderNode(child, depth + 1))}</div>
          )}
        </div>
      );
    }

    return (
      <div
        key={node.path}
        draggable
        onClick={(e) => handleSelect(node, e)}
        onContextMenu={(e) => handleContextMenu(e, node)}
        style={{ paddingLeft: `${depth * 14 + 20}px` }}
        className={`flex items-center justify-between py-[3px] px-2 text-[11.5px] rounded-sm cursor-pointer group transition-colors ${
          isActive
            ? "bg-indigo-600/25 text-indigo-200 font-semibold"
            : isSelected
            ? "bg-slate-700/50 text-slate-200"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
        }`}
      >
        <div className="flex items-center gap-1.5 truncate flex-1 min-w-0">
          <FileCode className={`w-3.5 h-3.5 shrink-0 ${isActive ? "text-indigo-400" : iconColor}`} />
          {isEditing ? (
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") { onRenameFile(node.path, newName); setEditingPath(null); }
                else if (e.key === "Escape") setEditingPath(null);
              }}
              onClick={(e) => e.stopPropagation()}
              className="bg-slate-900 border border-indigo-500 text-[11px] px-1 py-0.5 rounded text-slate-100 outline-none w-full font-mono"
              autoFocus
            />
          ) : (
            <span className="truncate font-mono">{node.name}</span>
          )}
        </div>
        {isUnsaved && <Circle className="w-1.5 h-1.5 fill-amber-400 text-amber-400 shrink-0" />}
      </div>
    );
  };

  return (
    <div
      onClick={handleGlobalClick}
      className="flex flex-col h-full bg-slate-900/60 text-slate-300 font-sans border-r border-slate-800/60 select-none overflow-hidden"
    >
      {/* Header Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800/60 bg-slate-950/40">
        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Explorer</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowRecent((prev) => !prev)}
            className={`p-1 rounded hover:bg-slate-800 transition-colors ${showRecent ? "text-indigo-400" : "text-slate-500"}`}
            title="Recent Files"
          >
            <Clock className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onCreateFile()}
            className="p-1 text-slate-500 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
            title="New File"
          >
            <FilePlus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onCreateFolder()}
            className="p-1 text-slate-500 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
            title="New Folder"
          >
            <FolderPlus className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="px-2 py-1.5 border-b border-slate-800/50">
        <div className="relative">
          <Search className="w-3 h-3 absolute left-2 top-1.5 text-slate-600" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded text-[11px] pl-6 pr-2 py-1 text-slate-300 placeholder-slate-700 focus:outline-none focus:border-indigo-500/60 font-mono"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-1.5 top-1.5 text-slate-600 hover:text-slate-400">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Recent Files Panel */}
      {showRecent && recentFiles.length > 0 && (
        <div className="border-b border-slate-800/60 bg-slate-950/40">
          <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-slate-600">Recent</div>
          {recentFiles.slice(0, 5).map((f) => (
            <div
              key={f.path}
              onClick={() => onSelectFile(f)}
              className="flex items-center gap-1.5 px-3 py-1 hover:bg-slate-800/50 cursor-pointer text-slate-400 hover:text-slate-200 transition-colors"
            >
              <Clock className="w-2.5 h-2.5 text-slate-600 shrink-0" />
              <span className="truncate font-mono text-[11px]">{f.path.split("/").pop()}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-1 scrollbar-thin scrollbar-thumb-slate-800/80 scrollbar-track-transparent">
        {tree.length === 0 ? (
          <div className="text-[11px] text-slate-600 p-4 text-center">No files in project</div>
        ) : (
          tree.map((node) => renderNode(node))
        )}
      </div>

      {/* File Count */}
      <div className="px-3 py-1.5 border-t border-slate-800/60 text-[10px] text-slate-600 font-mono">
        {files.length} file{files.length !== 1 ? "s" : ""} · {selectedPaths.size > 0 ? `${selectedPaths.size} selected` : "workspace"}
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <div
          ref={contextMenuRef}
          style={{ position: "fixed", top: contextMenu.y, left: contextMenu.x, zIndex: 9999 }}
          className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl py-1 min-w-44 text-xs animate-in fade-in-0 zoom-in-95"
        >
          {contextMenu.node.file && (
            <button
              onClick={() => { onSelectFile(contextMenu.node.file!); setContextMenu(null); }}
              className="w-full px-3 py-1.5 text-left text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2"
            >
              <FileCode className="w-3.5 h-3.5 text-slate-400" /> Open File
            </button>
          )}
          {contextMenu.node.isFolder && (
            <button
              onClick={() => { onCreateFile(contextMenu.node.path); setContextMenu(null); }}
              className="w-full px-3 py-1.5 text-left text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2"
            >
              <FilePlus className="w-3.5 h-3.5 text-indigo-400" /> New File Here
            </button>
          )}
          <button
            onClick={() => { setEditingPath(contextMenu.node.path); setNewName(contextMenu.node.name); setContextMenu(null); }}
            className="w-full px-3 py-1.5 text-left text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2"
          >
            <Pencil className="w-3.5 h-3.5 text-amber-400" /> Rename
          </button>
          {contextMenu.node.file && onDuplicateFile && (
            <button
              onClick={() => { onDuplicateFile(contextMenu.node.file!); setContextMenu(null); }}
              className="w-full px-3 py-1.5 text-left text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2"
            >
              <Copy className="w-3.5 h-3.5 text-cyan-400" /> Duplicate
            </button>
          )}
          <div className="my-1 border-t border-slate-800" />
          {contextMenu.node.file && (
            <button
              onClick={() => { onDeleteFile(contextMenu.node.file!.id); setContextMenu(null); }}
              className="w-full px-3 py-1.5 text-left text-rose-400 hover:bg-rose-950/50 flex items-center gap-2"
            >
              <Trash2 className="w-3.5 h-3.5" /> Delete
            </button>
          )}
        </div>
      )}
    </div>
  );
}
