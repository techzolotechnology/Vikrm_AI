import { useCallback, useEffect, useMemo, useRef, useState, type DragEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  addEdge,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
  type OnConnect,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  ArrowLeft,
  Save,
  Bot,
  MessageSquare,
  Wrench,
  Undo2,
  Redo2,
  Trash2,
  CheckCircle2,
  Loader2,
  Maximize2,
  LayoutGrid,
  Play,
  Info,
  Keyboard,
  X,
} from "lucide-react";

import { NodeConfigPanel } from "@/components/workflow/node-config-panel";
import { nodeTypes } from "@/components/workflow/nodes";
import { NodePalette } from "@/components/workflow/node-palette";
import { RunPanel } from "@/components/workflow/run-panel";
import { Tooltip } from "@/components/ui/tooltip";
import { useRunWorkflow, useUpdateWorkflow, useWorkflow, useWorkflowRuns } from "@/hooks/use-workflows";
import { cn } from "@/lib/utils";
import type { WorkflowNodeData, WorkflowNodeType } from "@/types/workflow";

// ─── Templates ────────────────────────────────────────────────────────────────

const STARTER_TEMPLATES = [
  {
    title: "AI Chat",
    desc: "Start → LLM → Output",
    icon: MessageSquare,
    color: "#7C3AED",
    nodes: [
      { id: "start", type: "start", position: { x: 100, y: 220 }, data: {} },
      { id: "llm_1", type: "llm", position: { x: 380, y: 220 }, data: { prompt: "Respond helpfully to: {{input}}", provider: "ollama", model: "llama3.2", temperature: 0.7 } },
      { id: "output_1", type: "output", position: { x: 660, y: 220 }, data: { template: "{{llm_1.output}}" } },
    ],
    edges: [
      { id: "e1", source: "start", target: "llm_1", animated: true },
      { id: "e2", source: "llm_1", target: "output_1", animated: true },
    ],
  },
  {
    title: "Research Agent",
    desc: "Start → Agent → Output",
    icon: Bot,
    color: "#22D3EE",
    nodes: [
      { id: "start", type: "start", position: { x: 100, y: 220 }, data: {} },
      { id: "agent_1", type: "agent", position: { x: 380, y: 220 }, data: { prompt: "Research and summarize: {{input}}" } },
      { id: "output_1", type: "output", position: { x: 660, y: 220 }, data: { template: "{{agent_1.output}}" } },
    ],
    edges: [
      { id: "e1", source: "start", target: "agent_1", animated: true },
      { id: "e2", source: "agent_1", target: "output_1", animated: true },
    ],
  },
  {
    title: "Tool Pipeline",
    desc: "Start → Tool → LLM → Output",
    icon: Wrench,
    color: "#F59E0B",
    nodes: [
      { id: "start", type: "start", position: { x: 80, y: 220 }, data: {} },
      { id: "tool_1", type: "tool", position: { x: 320, y: 220 }, data: { tool_name: "calculator", input: "{{input}}" } },
      { id: "llm_1", type: "llm", position: { x: 560, y: 220 }, data: { prompt: "Explain this result: {{tool_1.output}}", provider: "ollama", model: "llama3.2" } },
      { id: "output_1", type: "output", position: { x: 800, y: 220 }, data: { template: "{{llm_1.output}}" } },
    ],
    edges: [
      { id: "e1", source: "start", target: "tool_1", animated: true },
      { id: "e2", source: "tool_1", target: "llm_1", animated: true },
      { id: "e3", source: "llm_1", target: "output_1", animated: true },
    ],
  },
];

const DEFAULT_DATA: Record<WorkflowNodeType, WorkflowNodeData> = {
  start: {},
  llm: { prompt: "{{input}}", provider: "ollama", model: "llama3.2", temperature: 0.7 },
  agent: { prompt: "{{input}}" },
  condition: { left: "{{input}}", operator: "contains", right: "" },
  tool: { tool_name: "calculator", input: "{{input}}" },
  output: { template: "{{input}}" },
};

let nodeIdCounter = 10;

// ─── History Management ────────────────────────────────────────────────────────

interface HistoryEntry {
  nodes: Node[];
  edges: Edge[];
}

function useHistory(initialNodes: Node[], initialEdges: Edge[]) {
  const [history, setHistory] = useState<HistoryEntry[]>([{ nodes: initialNodes, edges: initialEdges }]);
  const [historyIndex, setHistoryIndex] = useState(0);

  const pushHistory = useCallback((nodes: Node[], edges: Edge[]) => {
    setHistory((prev) => {
      const newHistory = prev.slice(0, historyIndex + 1);
      return [...newHistory, { nodes: [...nodes], edges: [...edges] }];
    });
    setHistoryIndex((prev) => prev + 1);
  }, [historyIndex]);

  const undo = useCallback(() => {
    if (historyIndex > 0) {
      setHistoryIndex((prev) => prev - 1);
      return history[historyIndex - 1];
    }
    return null;
  }, [history, historyIndex]);

  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex((prev) => prev + 1);
      return history[historyIndex + 1];
    }
    return null;
  }, [history, historyIndex]);

  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < history.length - 1;

  return { pushHistory, undo, redo, canUndo, canRedo };
}

// ─── Shortcut Help Dialog ─────────────────────────────────────────────────────

function ShortcutsHelp({ onClose }: { onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="glass-card w-full max-w-md p-6 border border-border/80 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-sm font-bold text-white flex items-center gap-2">
            <Keyboard className="h-4 w-4 text-accent" />
            Workflow Builder Shortcuts
          </h3>
          <button onClick={onClose} className="text-white/40 hover:text-white transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-2.5">
          {[
            ["Ctrl+S", "Save workflow"],
            ["Ctrl+Z", "Undo last action"],
            ["Ctrl+Y / Ctrl+Shift+Z", "Redo"],
            ["Delete / Backspace", "Delete selected node"],
            ["Ctrl+Scroll", "Zoom in/out"],
            ["Middle Mouse Drag", "Pan canvas"],
            ["Escape", "Deselect / close panel"],
            ["Drag from palette", "Add new node"],
          ].map(([key, desc]) => (
            <div key={key} className="flex items-center justify-between gap-4">
              <span className="text-xs text-white/60">{desc}</span>
              <div className="flex items-center gap-1">
                {key.split(" / ").map((k) => (
                  <kbd key={k} className="rounded-md bg-white/10 border border-white/15 px-2 py-0.5 font-mono text-[10px] text-white/80 whitespace-nowrap">
                    {k}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Builder Canvas ───────────────────────────────────────────────────────────

function BuilderCanvas({ workflowId }: { workflowId: number }) {
  const navigate = useNavigate();
  const { data: workflow } = useWorkflow(workflowId);
  const updateWorkflow = useUpdateWorkflow(workflowId);
  const runWorkflow = useRunWorkflow(workflowId);
  const { data: runs = [] } = useWorkflowRuns(workflowId);
  const { screenToFlowPosition, fitView } = useReactFlow();

  const [workflowName, setWorkflowName] = useState("");
  const [hasLoaded, setHasLoaded] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [showRunPanel, setShowRunPanel] = useState(false);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const initialNodes = useMemo<Node[]>(
    () => (workflow?.definition.nodes as Node[]) ?? [],
    [workflow?.definition.nodes],
  );
  const initialEdges = useMemo<Edge[]>(
    () =>
      (workflow?.definition.edges ?? []).map((e) => ({
        id: e.id ?? `${e.source}-${e.target}-${e.branch ?? ""}`,
        source: e.source,
        target: e.target,
        sourceHandle: e.branch ?? undefined,
        animated: true,
        style: { stroke: "#7C3AED", strokeWidth: 2 },
      })) as Edge[],
    [workflow?.definition.edges],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const { pushHistory, undo, redo, canUndo, canRedo } = useHistory(initialNodes, initialEdges);

  if (workflow && !hasLoaded) {
    setNodes(initialNodes);
    setEdges(initialEdges);
    setWorkflowName(workflow.name);
    setHasLoaded(true);
  }

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => {
        const newEdges = addEdge({
          ...connection,
          animated: true,
          style: { stroke: "#7C3AED", strokeWidth: 2 },
        }, eds);
        pushHistory(nodes, newEdges);
        return newEdges;
      });
    },
    [setEdges, nodes, pushHistory],
  );

  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault();
      const nodeType = event.dataTransfer.getData("application/vikrm-node-type") as WorkflowNodeType;
      if (!nodeType) return;

      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      const id = `node_${nodeIdCounter++}`;
      const newNode: Node = {
        id,
        type: nodeType,
        position,
        data: DEFAULT_DATA[nodeType] as Record<string, unknown>,
      };
      setNodes((nds) => {
        const updated = [...nds, newNode];
        pushHistory(updated, edges);
        return updated;
      });
    },
    [screenToFlowPosition, setNodes, edges, pushHistory],
  );

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  // ─── Auto-save with debounce ───
  const scheduleAutoSave = useCallback(() => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      handleSave(true);
    }, 3000);
  }, [nodes, edges, workflowName]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const handleSave = useCallback((silent = false) => {
    const definition = {
      nodes: nodes.map((n) => ({ id: n.id, type: n.type, data: n.data, position: n.position })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        branch: e.sourceHandle ?? null,
      })),
    };
    updateWorkflow.mutate(
      { name: workflowName || workflow?.name || "Untitled Workflow", definition: definition as never },
      { onSuccess: () => { if (!silent) setSavedAt(new Date()); } },
    );
    if (!silent) setSavedAt(new Date());
  }, [nodes, edges, workflowName, updateWorkflow, workflow?.name]);

  // ─── Keyboard Shortcuts ───
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput = target.tagName === "INPUT" || target.tagName === "TEXTAREA";

      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        handleSave(false);
        return;
      }

      if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        const prev = undo();
        if (prev) { setNodes(prev.nodes); setEdges(prev.edges); }
        return;
      }

      if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.shiftKey && e.key === "z"))) {
        e.preventDefault();
        const next = redo();
        if (next) { setNodes(next.nodes); setEdges(next.edges); }
        return;
      }

      if (!isInput && (e.key === "Delete" || e.key === "Backspace") && selectedNodeId) {
        e.preventDefault();
        setNodes((nds) => {
          const updated = nds.filter((n) => n.id !== selectedNodeId);
          pushHistory(updated, edges);
          return updated;
        });
        setEdges((eds) => eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId));
        setSelectedNodeId(null);
        return;
      }

      if (e.key === "Escape") {
        setSelectedNodeId(null);
      }

      if (e.key === "?" && !isInput) {
        setShowShortcuts(true);
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleSave, undo, redo, selectedNodeId, setNodes, setEdges, pushHistory, edges]);

  const applyTemplate = (template: typeof STARTER_TEMPLATES[0]) => {
    const newNodes = template.nodes as Node[];
    const newEdges = template.edges as Edge[];
    setNodes(newNodes);
    setEdges(newEdges);
    pushHistory(newNodes, newEdges);
    setTimeout(() => fitView({ padding: 0.2, duration: 600 }), 100);
  };

  const handleRunWorkflow = async (input: string) => {
    const definition = {
      nodes: nodes.map((n) => ({ id: n.id, type: n.type, data: n.data, position: n.position })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        branch: e.sourceHandle ?? null,
      })),
    };
    await updateWorkflow.mutateAsync({
      name: workflowName || workflow?.name || "Untitled Workflow",
      definition: definition as never,
    });
    runWorkflow.mutate(input);
  };

  const handleAutoLayout = () => {
    // Simple auto layout: space nodes evenly horizontally
    setNodes((nds) => {
      const sorted = [...nds].sort((a, b) => a.position.x - b.position.x);
      const updated = sorted.map((n, i) => ({
        ...n,
        position: { x: 100 + i * 280, y: 220 },
      }));
      pushHistory(updated, edges);
      return updated;
    });
    setTimeout(() => fitView({ padding: 0.2, duration: 600 }), 50);
  };

  const isRunning = runWorkflow.isPending || updateWorkflow.isPending;

  return (
    <div className="relative h-screen w-full" style={{ background: "hsl(240 10% 5%)" }}>
      {/* ─── Top Toolbar ─── */}
      <div className="absolute left-0 right-0 top-0 z-20 flex items-center justify-between gap-3 px-4 py-3 border-b border-white/8 bg-surface/80 backdrop-blur-xl">
        {/* Left group */}
        <div className="flex items-center gap-2.5">
          <Tooltip content="Back to workflows" side="bottom">
            <button
              onClick={() => navigate("/workflows")}
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-border/60 bg-surface/80 text-white/50 hover:border-primary/40 hover:text-white transition-all"
              aria-label="Back to workflows"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
          </Tooltip>

          <div className="flex items-center gap-2 rounded-xl border border-border/60 bg-surface/70 px-3 py-1.5">
            <div className="flex h-2 w-2 rounded-full bg-success animate-pulse" />
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              placeholder="Workflow Name..."
              className="bg-transparent font-display text-xs font-bold text-white placeholder:text-white/30 focus:outline-none w-40"
              aria-label="Workflow name"
            />
          </div>

          {savedAt && (
            <motion.div
              key={savedAt.toISOString()}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-1 font-mono text-[10px] text-success/70"
            >
              <CheckCircle2 className="h-3 w-3" />
              Saved {savedAt.toLocaleTimeString()}
            </motion.div>
          )}
        </div>

        {/* Center — Templates */}
        <div className="flex items-center gap-1.5">
          {STARTER_TEMPLATES.map((tmpl) => (
            <Tooltip key={tmpl.title} content={tmpl.desc} side="bottom">
              <motion.button
                whileHover={{ scale: 1.04, y: -1 }}
                whileTap={{ scale: 0.96 }}
                onClick={() => applyTemplate(tmpl)}
                className="flex items-center gap-1.5 rounded-xl border border-border/60 bg-surface/70 px-3 py-1.5 text-xs font-medium text-white/70 hover:border-primary/40 hover:text-white transition-all"
              >
                <tmpl.icon className="h-3 w-3" style={{ color: tmpl.color }} />
                {tmpl.title}
              </motion.button>
            </Tooltip>
          ))}
        </div>

        {/* Right group */}
        <div className="flex items-center gap-2">
          {/* Undo/Redo */}
          <div className="flex items-center gap-1 rounded-xl border border-border/60 bg-surface/70 p-1">
            <Tooltip content="Undo (Ctrl+Z)" side="bottom">
              <button
                onClick={() => { const prev = undo(); if (prev) { setNodes(prev.nodes); setEdges(prev.edges); } }}
                disabled={!canUndo}
                className="flex h-6 w-6 items-center justify-center rounded-lg text-white/50 hover:text-white disabled:opacity-30 transition-all"
                aria-label="Undo"
              >
                <Undo2 className="h-3.5 w-3.5" />
              </button>
            </Tooltip>
            <Tooltip content="Redo (Ctrl+Y)" side="bottom">
              <button
                onClick={() => { const next = redo(); if (next) { setNodes(next.nodes); setEdges(next.edges); } }}
                disabled={!canRedo}
                className="flex h-6 w-6 items-center justify-center rounded-lg text-white/50 hover:text-white disabled:opacity-30 transition-all"
                aria-label="Redo"
              >
                <Redo2 className="h-3.5 w-3.5" />
              </button>
            </Tooltip>
          </div>

          {/* Auto-layout */}
          <Tooltip content="Auto-arrange nodes" side="bottom">
            <button
              onClick={handleAutoLayout}
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-border/60 bg-surface/70 text-white/50 hover:border-accent/40 hover:text-accent transition-all"
              aria-label="Auto layout"
            >
              <LayoutGrid className="h-3.5 w-3.5" />
            </button>
          </Tooltip>

          {/* Fit view */}
          <Tooltip content="Fit to view" side="bottom">
            <button
              onClick={() => fitView({ padding: 0.2, duration: 500 })}
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-border/60 bg-surface/70 text-white/50 hover:border-accent/40 hover:text-accent transition-all"
              aria-label="Fit view"
            >
              <Maximize2 className="h-3.5 w-3.5" />
            </button>
          </Tooltip>

          {/* Delete selected */}
          <AnimatePresence>
            {selectedNodeId && selectedNodeId !== "start" && (
              <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }}>
                <Tooltip content="Delete selected node (Del)" side="bottom">
                  <button
                    onClick={() => {
                      setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId));
                      setEdges((eds) => eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId));
                      setSelectedNodeId(null);
                    }}
                    className="flex h-8 w-8 items-center justify-center rounded-xl border border-danger/40 bg-danger/10 text-danger hover:bg-danger/20 transition-all"
                    aria-label="Delete node"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </Tooltip>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Run */}
          <Tooltip content="Run workflow" side="bottom">
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => setShowRunPanel((v) => !v)}
              className={cn(
                "flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-bold text-white shadow-lg transition-all",
                showRunPanel
                  ? "bg-primary/30 border border-primary/50"
                  : "bg-gradient-brand shadow-glow-sm",
              )}
            >
              {isRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" strokeWidth={2} />}
              {isRunning ? "Running..." : "Run"}
            </motion.button>
          </Tooltip>

          {/* Save */}
          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => handleSave(false)}
            disabled={updateWorkflow.isPending}
            className="flex items-center gap-1.5 rounded-xl border border-border/60 bg-surface/70 px-3.5 py-1.5 text-xs font-bold text-white hover:border-primary/50 disabled:opacity-50 transition-all"
            aria-label="Save workflow"
          >
            {updateWorkflow.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" strokeWidth={2} />}
            Save
          </motion.button>

          {/* Shortcuts */}
          <Tooltip content="Keyboard shortcuts (?)" side="bottom">
            <button
              onClick={() => setShowShortcuts(true)}
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-border/60 bg-surface/70 text-white/40 hover:text-white transition-all"
              aria-label="Show keyboard shortcuts"
            >
              <Info className="h-3.5 w-3.5" />
            </button>
          </Tooltip>
        </div>
      </div>

      {/* ─── Node Palette ─── */}
      <NodePalette />

      {/* ─── React Flow Canvas ─── */}
      <div className="absolute inset-0 pt-[52px]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={(changes) => {
            onNodesChange(changes);
            scheduleAutoSave();
          }}
          onEdgesChange={(changes) => {
            onEdgesChange(changes);
            scheduleAutoSave();
          }}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          onNodeClick={(_, node) => setSelectedNodeId(node.id)}
          onPaneClick={() => setSelectedNodeId(null)}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={{
            animated: true,
            style: { stroke: "#7C3AED", strokeWidth: 2 },
          }}
          colorMode="dark"
          fitView
          snapToGrid
          snapGrid={[16, 16]}
          multiSelectionKeyCode="Shift"
          deleteKeyCode={null} // we handle it ourselves
          proOptions={{ hideAttribution: true }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={20}
            color="rgba(255,255,255,0.05)"
            size={1.5}
          />
          <Controls
            className="!bottom-6 !left-[272px] !rounded-xl !overflow-hidden !border !border-border/60 !bg-surface/80 !backdrop-blur-xl"
            showInteractive={false}
          />
          <MiniMap
            position="bottom-right"
            className="!bottom-6 !right-4 !bg-surface/90 !border !border-border/60 !rounded-2xl shadow-xl overflow-hidden"
            nodeColor={(n) => {
              const colors: Record<string, string> = {
                start: "#22C55E",
                llm: "#7C3AED",
                agent: "#22D3EE",
                condition: "#F59E0B",
                tool: "#F59E0B",
                output: "#EC4899",
              };
              return colors[n.type ?? ""] ?? "#64748B";
            }}
            maskColor="rgba(0,0,0,0.6)"
          />
        </ReactFlow>
      </div>

      {/* ─── Properties Panel ─── */}
      <AnimatePresence>
        {selectedNode && (
          <NodeConfigPanel
            node={{
              id: selectedNode.id,
              type: selectedNode.type as WorkflowNodeType,
              data: selectedNode.data as WorkflowNodeData,
              position: selectedNode.position,
            }}
            onChange={(data) =>
              setNodes((nds) => nds.map((n) => (n.id === selectedNode.id ? { ...n, data } : n)))
            }
            onClose={() => setSelectedNodeId(null)}
            onDelete={() => {
              setNodes((nds) => {
                const updated = nds.filter((n) => n.id !== selectedNode.id);
                pushHistory(updated, edges);
                return updated;
              });
              setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
              setSelectedNodeId(null);
            }}
          />
        )}
      </AnimatePresence>

      {/* ─── Run Panel ─── */}
      <AnimatePresence>
        {showRunPanel && (
          <RunPanel
            onRun={handleRunWorkflow}
            isRunning={isRunning}
            latestRun={runWorkflow.data ?? runs[0]}
            onClose={() => setShowRunPanel(false)}
          />
        )}
      </AnimatePresence>

      {/* ─── Shortcuts Dialog ─── */}
      <AnimatePresence>
        {showShortcuts && <ShortcutsHelp onClose={() => setShowShortcuts(false)} />}
      </AnimatePresence>

      {/* ─── Node count indicator ─── */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
        <div className="flex items-center gap-2 rounded-full border border-border/60 bg-surface/80 px-3 py-1 backdrop-blur-xl">
          <span className="font-mono text-[10px] text-white/40">
            {nodes.length} nodes · {edges.length} edges
          </span>
          {selectedNodeId && (
            <span className="font-mono text-[10px] text-accent">
              · Selected: {selectedNodeId}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Exports ──────────────────────────────────────────────────────────────────

export function WorkflowBuilder() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const id = Number(workflowId);

  if (!workflowId || Number.isNaN(id)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-white/50">
        Invalid workflow ID specified.
      </div>
    );
  }

  return (
    <ReactFlowProvider>
      <BuilderCanvas workflowId={id} />
    </ReactFlowProvider>
  );
}
