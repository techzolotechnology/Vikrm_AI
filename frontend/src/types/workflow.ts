export type WorkflowNodeType = "start" | "llm" | "agent" | "condition" | "tool" | "output";

export interface WorkflowNodeData {
  [key: string]: unknown;
  prompt?: string;
  provider?: string;
  model?: string;
  temperature?: number;
  agent_id?: number;
  left?: string;
  operator?: string;
  right?: string;
  tool_name?: string;
  input?: string;
  template?: string;
}

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  data: WorkflowNodeData;
  position: { x: number; y: number };
}

export interface WorkflowEdge {
  id?: string;
  source: string;
  target: string;
  branch?: "true" | "false" | null;
}

export interface WorkflowDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Workflow {
  id: number;
  name: string;
  description: string | null;
  definition: WorkflowDefinition;
  created_at: string;
  updated_at: string;
}

export interface WorkflowStep {
  node_id: string;
  node_type: string;
  status: "success" | "failed";
  input_summary: string;
  output: string;
  error: string | null;
  started_at: string;
  completed_at: string;
}

export interface WorkflowRun {
  id: number;
  workflow_id: number;
  status: "running" | "completed" | "failed";
  initial_input: string;
  final_output: string | null;
  steps: WorkflowStep[];
  error: string | null;
  started_at: string;
  completed_at: string | null;
}
