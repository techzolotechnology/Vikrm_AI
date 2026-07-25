import { useCallback, useMemo, useState, type DragEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  addEdge,
  Background,
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
} from "lucide-react";

import { NodeConfigPanel } from "@/components/workflow/node-config-panel";
import { nodeTypes } from "@/components/workflow/nodes";
import { NodePalette } from "@/components/workflow/node-palette";
import { RunPanel } from "@/components/workflow/run-panel";
import { useRunWorkflow, useUpdateWorkflow, useWorkflow, useWorkflowRuns } from "@/hooks/use-workflows";
import type { WorkflowNodeData, WorkflowNodeType } from "@/types/workflow";

const DEFAULT_DATA: Record<WorkflowNodeType, WorkflowNodeData> = {
  start: {},
  llm: { prompt: "{{input}}", provider: "ollama", model: "llama3.2", temperature: 0.7 },
  agent: { prompt: "{{input}}" },
  condition: { left: "{{input}}", operator: "contains", right: "" },
  tool: { tool_name: "calculator", input: "{{input}}" },
  output: { template: "{{input}}" },
};

const STARTER_TEMPLATES = [
  {
    title: "AI Chatbot Pipeline",
    desc: "Start → LLM → Output",
    icon: MessageSquare,
    nodes: [
      { id: "start", type: "start", position: { x: 100, y: 200 }, data: {} },
      { id: "llm_1", type: "llm", position: { x: 380, y: 200 }, data: { prompt: "Respond to: {{input}}", provider: "ollama", model: "llama3.2" } },
      { id: "output_1", type: "output", position: { x: 680, y: 200 }, data: { template: "{{llm_1.output}}" } },
    ],
    edges: [
      { id: "e1", source: "start", target: "llm_1" },
      { id: "e2", source: "llm_1", target: "output_1" },
    ],
  },
  {
    title: "Research Agent Workflow",
    desc: "Start → Autonomous Agent → Output",
    icon: Bot,
    nodes: [
      { id: "start", type: "start", position: { x: 100, y: 200 }, data: {} },
      { id: "agent_1", type: "agent", position: { x: 380, y: 200 }, data: { prompt: "Research topic: {{input}}" } },
      { id: "output_1", type: "output", position: { x: 680, y: 200 }, data: { template: "{{agent_1.output}}" } },
    ],
    edges: [
      { id: "e1", source: "start", target: "agent_1" },
      { id: "e2", source: "agent_1", target: "output_1" },
    ],
  },
  {
    title: "Tool Execution Pipeline",
    desc: "Start → Calculator Tool → Output",
    icon: Wrench,
    nodes: [
      { id: "start", type: "start", position: { x: 100, y: 200 }, data: {} },
      { id: "tool_1", type: "tool", position: { x: 380, y: 200 }, data: { tool_name: "calculator", input: "{{input}}" } },
      { id: "output_1", type: "output", position: { x: 680, y: 200 }, data: { template: "{{tool_1.output}}" } },
    ],
    edges: [
      { id: "e1", source: "start", target: "tool_1" },
      { id: "e2", source: "tool_1", target: "output_1" },
    ],
  },
];

let nodeIdCounter = 10;

function BuilderCanvas({ workflowId }: { workflowId: number }) {
  const navigate = useNavigate();
  const { data: workflow } = useWorkflow(workflowId);
  const updateWorkflow = useUpdateWorkflow(workflowId);
  const runWorkflow = useRunWorkflow(workflowId);
  const { data: runs = [] } = useWorkflowRuns(workflowId);
  const { screenToFlowPosition } = useReactFlow();

  const [workflowName, setWorkflowName] = useState("");

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
      })) as Edge[],
    [workflow?.definition.edges],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);

  if (workflow && !hasLoaded) {
    setNodes(initialNodes);
    setEdges(initialEdges);
    setWorkflowName(workflow.name);
    setHasLoaded(true);
  }

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges],
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
      setNodes((nds) => [...nds, newNode]);
    },
    [screenToFlowPosition, setNodes],
  );

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  const handleSave = () => {
    const definition = {
      nodes: nodes.map((n) => ({ id: n.id, type: n.type, data: n.data, position: n.position })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        branch: e.sourceHandle ?? null,
      })),
    };
    updateWorkflow.mutate({
      name: workflowName || workflow?.name || "Untitled Workflow",
      definition: definition as never,
    });
  };

  const applyTemplate = (template: typeof STARTER_TEMPLATES[0]) => {
    setNodes(template.nodes as Node[]);
    setEdges(template.edges as Edge[]);
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

  return (
    <div className="relative h-screen w-full aurora-bg" style={{ background: "hsl(240 10% 5%)" }}>
      {/* Top Toolbar */}
      <div className="absolute left-4 right-4 top-4 z-20 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-2 pointer-events-auto">
          <button
            onClick={() => navigate("/workflows")}
            className="flex h-9 w-9 items-center justify-center rounded-2xl border border-border/80 bg-surface/90 text-white/60 hover:border-primary/40 hover:text-white transition-all backdrop-blur-xl shadow-lg"
            title="Back to Workflows"
          >
            <ArrowLeft className="h-4 w-4" strokeWidth={1.75} />
          </button>

          <div className="flex items-center gap-2 rounded-2xl border border-border/80 bg-surface/90 px-3.5 py-1.5 backdrop-blur-xl shadow-lg">
            <span className="h-2 w-2 rounded-full bg-success shadow-glow-sm" />
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              placeholder="Workflow Name..."
              className="bg-transparent font-display text-xs font-bold text-white placeholder:text-white/30 focus:outline-none w-44"
            />
            <span className="rounded-full bg-white/5 border border-white/10 px-2 py-0.5 font-mono text-[9px] text-accent">
              Auto-Save Ready
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 pointer-events-auto">
          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            onClick={handleSave}
            disabled={updateWorkflow.isPending}
            className="flex items-center gap-1.5 rounded-2xl bg-gradient-brand px-4 py-2 text-xs font-bold text-white shadow-glow-sm transition disabled:opacity-50"
          >
            <Save className="h-3.5 w-3.5" strokeWidth={2} />
            {updateWorkflow.isPending ? "Saving..." : "Save Workflow"}
          </motion.button>
        </div>
      </div>

      <NodePalette />

      {/* Starter Template Bar if workflow has 1 or fewer nodes */}
      {nodes.length <= 1 && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-20 flex gap-2">
          {STARTER_TEMPLATES.map((tmpl) => (
            <motion.button
              key={tmpl.title}
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => applyTemplate(tmpl)}
              className="flex items-center gap-2 rounded-2xl border border-primary/30 bg-surface/90 px-3.5 py-2 text-xs font-medium text-white shadow-xl backdrop-blur-xl hover:border-primary transition"
            >
              <tmpl.icon className="h-3.5 w-3.5 text-accent" />
              <span>Insert {tmpl.title}</span>
            </motion.button>
          ))}
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
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
      >
        <Background gap={24} color="rgba(255,255,255,0.06)" size={1} />
        <Controls className="!bottom-28 !left-4" />
        <MiniMap
          position="bottom-left"
          className="!bottom-4 !left-4 !bg-surface/90 !border !border-border/80 !rounded-2xl shadow-xl overflow-hidden backdrop-blur-xl"
          nodeColor="#7C3AED"
          maskColor="rgba(0, 0, 0, 0.7)"
        />
      </ReactFlow>

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
            setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
            setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
            setSelectedNodeId(null);
          }}
        />
      )}

      <RunPanel
        onRun={handleRunWorkflow}
        isRunning={runWorkflow.isPending || updateWorkflow.isPending}
        latestRun={runWorkflow.data ?? runs[0]}
      />
    </div>
  );
}

export function WorkflowBuilder() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const id = Number(workflowId);

  if (!workflowId || Number.isNaN(id)) {
    return <div className="p-10 text-white/50">Invalid workflow ID specified.</div>;
  }

  return (
    <ReactFlowProvider>
      <BuilderCanvas workflowId={id} />
    </ReactFlowProvider>
  );
}
