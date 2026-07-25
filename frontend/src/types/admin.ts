export interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: "admin" | "user";
  is_active: boolean;
  created_at: string;
}

export interface SystemStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  total_conversations: number;
  total_agents: number;
  total_teams: number;
  total_memories: number;
  total_documents: number;
  total_workflows: number;
  total_tool_executions: number;
}
