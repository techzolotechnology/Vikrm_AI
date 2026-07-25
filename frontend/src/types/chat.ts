export interface ChatMessage {
  id: number;
  role: "system" | "user" | "assistant";
  content: string;
  error: string | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  provider: string;
  model: string;
  agent_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}
