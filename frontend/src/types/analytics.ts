export interface StatusBreakdown {
  completed: number;
  failed: number;
  running: number;
}

export interface DashboardStats {
  total_conversations: number;
  total_messages: number;
  total_agents: number;
  total_teams: number;
  total_memories: number;
  total_documents: number;
  documents_ready: number;
  documents_failed: number;
  total_workflows: number;
  workflow_runs: StatusBreakdown;
  team_runs: StatusBreakdown;
  total_tool_executions: number;
  tool_executions_success: number;
  tool_executions_failed: number;
}

export interface ActivityItem {
  type: "conversation" | "workflow_run" | "team_run" | "tool_execution" | "document";
  title: string;
  status: string | null;
  timestamp: string;
}
