export interface Memory {
  id: number;
  content: string;
  memory_type: "fact" | "preference" | "context";
  agent_id: number | null;
  is_pinned?: boolean;
  is_archived?: boolean;
  created_at: string;
}
