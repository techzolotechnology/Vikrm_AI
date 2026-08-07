export interface Agent {
  id: number;
  name: string;
  description: string | null;
  avatar_color: string;
  instructions: string | null;
  goal: string | null;
  personality: string | null;
  provider: string;
  model: string;
  temperature: number;
  max_tokens: number;
  version?: number;
  status: "active" | "archived";
  created_at: string;
  updated_at: string;
}

export interface CreateAgentPayload {
  name: string;
  description?: string;
  avatar_color?: string;
  instructions?: string;
  goal?: string;
  personality?: string;
  provider?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}
