export interface Memory {
  id: number;
  content: string;
  memory_type: "fact" | "preference" | "context";
  agent_id: number | null;
  created_at: string;
}
