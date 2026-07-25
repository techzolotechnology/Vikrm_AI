export interface AgentTeam {
  id: number;
  name: string;
  description: string | null;
  manager_agent_id: number;
  member_agent_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface TeamRunStep {
  agent_name: string;
  subtask: string;
  output: string;
  status: "success" | "failed";
  error: string | null;
}

export interface TeamRun {
  id: number;
  team_id: number;
  task: string;
  status: "running" | "completed" | "failed";
  plan: Record<string, unknown>[];
  steps: TeamRunStep[];
  final_output: string | null;
  error: string | null;
  started_at: string;
  completed_at: string | null;
}
